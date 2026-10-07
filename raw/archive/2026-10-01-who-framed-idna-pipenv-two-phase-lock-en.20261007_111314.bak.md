---
title: "The Package That Took the Blame: A pipenv ResolutionImpossible Mystery and the Two-Phase Lock Behind It"
date: 2026-10-01
categories: [engineering, python, debugging]
tags: [pipenv, pip, dependency-resolution, idna, PEP592, ResolutionImpossible]
---

# The Package That Took the Blame: A pipenv ResolutionImpossible Mystery and the Two-Phase Lock Behind It

In the previous post, [*The Night pip Stopped Working*](/), we climbed over Ubuntu 24.04's two walls and finally got `pipenv` running. I thought the job was done. Instead the real show began: `pipenv lock` threw a `ResolutionImpossible` and flatly accused `idna==3.7`.

I chased its accusation everywhere — fixed the Python version, upgraded a yanked package — and the error didn't budge. Then I handed the *same* dependency set to `pip` directly, and **it resolved on the first try.** Which turned the bug into a far more interesting mystery: **identical inputs, so why can pip solve it and pipenv can't? And the package pipenv fingered as the culprit is innocent.**

This is the post-mortem of that false accusation — and it digs out the `pipenv` two-phase locking mechanism that most developers have never looked at.

---

## TL;DR

- `pipenv lock` fails with `ResolutionImpossible`, "The user requested idna==3.7". But feeding the **exact same** dependency set to `pip install --dry-run` **succeeds** — idna 3.7 installs fine.
- Two tools, same input, different verdicts → the problem isn't the dependency math, it's the **resolution process**.
- The truth: **pipenv locks in two phases** — first `[packages]` (default), then "default + `[dev-packages]`".
  - The default packages quietly pull idna in via `aiobotocore → aiohttp → yarl → idna(>=2.0)`, and phase 1 locks it to the **newest, 3.20**.
  - Phase 2 then meets the hard `idna==3.7` in `[dev-packages]`. `3.20 ≠ 3.7`, the two phases can't reconcile → boom.
- `pip` resolves default + dev in **one pass**, so it just picks 3.7 (which satisfies every constraint) and never hits the trap.
- Two red herrings along the way: wrong Python (3.12 vs 3.10) and a yanked `requests==2.32.0`. **I was certain the yanked requests was the cause — upgrading it still failed, and reality corrected me.**
- Fix: relax `idna = "3.7"` to `idna = ">=3.7"`; both phases converge on 3.20, CVE floor intact. But it's a **security-pin decision** — take it to the repo owner, don't change it unilaterally.

---

## The crime scene

The key lines of the repo's `Pipfile`:

```toml
[dev-packages]
requests = "2.32.0"
idna = "3.7"

[requires]
python_version = "3.10"
```

And `pipenv lock`, trimmed:

```text
Locking dependencies...
Resolving dependencies...
✔ Success!                          ← phase 1: locking [packages]
Locking dependencies...
Resolving dependencies...
✘ Locking Failed!                   ← phase 2: locking [dev-packages]
ERROR: ResolutionImpossible
The conflict is caused by:
    The user requested idna==3.7
```

## First cut: layer the output, ignore the traceback

Triage reflex: **classify each block before you read it.**

| Output block | What it is | Verdict |
|---|---|---|
| `Warning: Pipfile requires 3.10, but you are using 3.12.3` | wrong interpreter | red herring A |
| `✘ Locking Failed! … ResolutionImpossible … idna==3.7` | the real failure | signal |
| `Traceback … lock.py … resolver.py … raise exc` | pipenv's own call stack | **pure noise, ignore** |

That `lock.py:408 → resolver.py:2061` traceback is useless — it's just pipenv's stack on the way to re-raising. The signal is the `ResolutionImpossible` block *above* it.

## Two hypotheses, both falsified (what debugging actually looks like)

**Red herring A — the interpreter.** The venv was built on system 3.12 while the Pipfile pins 3.10. Re-locked under `docker python:3.10-slim` — the warning vanished, **but the idna error remained.** Ruled out.

**Red herring B — the yanked requests.** A line flickered past in `pip --dry-run`:

```text
WARNING: The candidate selected ... is a yanked version: 'requests' (2.32.0)
Reason: Yanked due to conflicts with CVE-2024-35195 mitigation
```

> **What "yanked" means (PEP 592)**: a maintainer flags a version "don't auto-pick me," but the file still exists and **still installs if pinned with an exact `==`**. This is a classic spot where pip and pipenv diverge.

I was sure: "that's it." I bumped requests to the non-yanked `2.32.5` — **pipenv failed anyway.** Corrected. That lesson deserves its own entry (see Q4).

## The decisive comparison: pip succeeds, pipenv fails

Hand the **same pinned set** straight to pip:

```bash
pip install --dry-run --index-url <nexus> \
  pysftp python-gnupg cryptography==44.0.1 urllib3==1.26.19 paramiko==3.4.0 \
  botocore aiobotocore boto3 pytest==7.4.0 moto==4.2.14 ... \
  requests==2.32.5 "idna==3.7" pytest-sftpserver==1.3.0
```

Result: **`Would install ... idna-3.7 ... requests-2.32.5 ...` — success.** That proves **no real version conflict exists**; idna 3.7 is fully compatible with the whole set. Since pip can solve it and pipenv can't, the difference must be in the **resolution process**.

## The real culprit: pipenv's two-phase lock

Notice the "✔ Success!" followed by "✘ Locking Failed!" — those are **two phases**, and pip never does this:

1. **Phase 1: lock `[packages]` (default) only → success.** Critically, the default packages pull idna in transitively: `aiobotocore → aiohttp → yarl → idna(>=2.0)`. Nothing in the default section pins idna, so it locks to the **newest**.
2. **Phase 2: default + `[dev-packages]` → fail.** Now the hard `idna==3.7` from dev must coexist with the newer idna phase 1 already chose. pipenv requires one version per package across both sections, so `idna==3.7` (dev) vs `idna==<newest>` (default-transitive) → unsolvable.

One command nails it — resolve only the default packages and see which idna gets locked:

```bash
pip install --dry-run --index-url <nexus> \
  pysftp python-gnupg cryptography==44.0.1 urllib3==1.26.19 paramiko==3.4.0 \
  botocore aiobotocore boto3 2>&1 | grep -i idna
```

Output:

```text
Collecting idna>=2.0            ← yarl's constraint
  Downloading idna-3.20         ← phase 1 picks the newest: 3.20
```

**3.20 vs 3.7 — mystery solved.** pip resolves default + dev in one pass and simply picks 3.7 (it satisfies every `>=`), so it never hits the trap; pipenv's phase 1 locks idna to 3.20 and phase 2 can never get back to 3.7.

## The fix: relax to `>=3.7`

```toml
idna = "3.7"     →     idna = ">=3.7"
```

Now phase 2 can accept phase 1's choice of 3.20, both phases converge, and the lock succeeds. The intent behind `idna==3.7` was almost certainly the **CVE-2024-3651** floor (the `idna.encode()` DoS, fixed in 3.7); relaxing to `>=3.7` yields 3.20 — **not weaker, strictly safer.**

> ⚠️ But this is a **security-pin decision**, not a mechanical edit. Why was 3.7 pinned in the dev section only? Was the intent merely the CVE floor? Those are the repo owner's call — don't loosen a security pin just to turn your own PR green.

---

## The interviewer's follow-up chain

**Q1: `ResolutionImpossible` vs `No matching distribution` — what's the difference?**
The first is "mutually exclusive constraints" — several requirements can't all hold (this case). The second is "that version isn't in the index at all." pipenv blurs both into `ResolutionImpossible`, which is why you drop to pip's own message to tell them apart.

**Q2: Why can pip solve it but not pipenv, with identical input?**
Because the **process differs**. pip resolves all requirements in one pass; pipenv resolves in two phases (default, then default+dev) and demands one version per package across them. The same pins are solvable one-pass and unsolvable two-phase. A tool's *process* shapes its *errors*.

**Q3: The error says "The user requested idna==3.7" — why is idna innocent?**
Because pip proved idna 3.7 has zero conflict with the full set. pipenv's "conflict is caused by X" is a *summary*, not the truth — it names the direct pin it was processing, while the real contradiction is "phase 1 locked idna to 3.20." When pipenv blames a package that pip installs happily, go read pip's output for `yanked` / the real constraint.

**Q4: You were certain it was the yanked requests, and you were wrong. The lesson?**
**Confirm a hypothesis by acting on it, not by how well the story holds together.** The yank warning was real and sounded causal, but it was irrelevant. The way to prove it irrelevant was to upgrade requests and re-lock — then watch it fail anyway. A hypothesis that sounds right is still just a hypothesis until a change you make from it reproduces the fix.

**Q5: How do you avoid this class of bug at the root?**
**Don't put a pin in the wrong section.** `idna==3.7` in `[dev-packages]` was fine as long as nothing else pulled idna. The moment a *default-section* dependency drags it in transitively (aiobotocore→aiohttp→yarl), the isolated dev pin collides with the default section's free choice. **Transitive deps don't respect your dev/prod split.** Pin in the section that's actually affected — or use a range, not a dead version.

**Q6: How did swapping to an internal PyPI proxy expose an old problem?**
Because **changing the index changes the set of available versions.** Public pypi.org keeps every old release; a firewalled proxy like Nexus quarantines some, so its set is a subset of PyPI's. Combine that with "newest keeps climbing" (idna is at 3.20 now) and a dead pin that resolved yesterday may be unsolvable today. **Your PR didn't create the problem — it revealed a latent pin.**

---

**Bottom line:** `ResolutionImpossible` pointed straight at idna and shouted "it's this one" — but idna was framed. The real culprit was pipenv's two-phase lock, plus a version pin placed in the wrong section that a default dependency happened to drag in transitively. Most people see the error and go move idna — the wrong direction. Understanding how a tool *searches* is worth more than understanding what it *prints*.
