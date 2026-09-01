---
title: "The CI Check That Never Ran Once Gave Us a Fake Green Checkmark"
date: 2026-08-04
categories: [engineering, python]
tags: [python, docker, ci-cd, github-actions, testing]
---

> "The first principle is that you must not fool yourself — and you are the easiest person to fool." — Richard Feynman

---

The last post covered the `_cffi_backend` incident that sat dormant for five months: build-time Python 3.11, runtime Python 3.10, one version number living in two places, artifacts silently mismatched until an unrelated formatting PR rebuilt 21 images at once and set the whole thing off.

This post isn't about that bug. It's about what happened **after** the fix shipped. Alex merged the PR, watched CI go green, and was about to move on to the next ticket — then stopped and asked himself one question:

> "What does this green checkmark actually prove?"

The answer turned out to be: almost nothing. The two new CI steps in that PR had **never once actually executed.**

## The 30-second version

Alex added a CI step that derives the build-time Python version from each image's own `Dockerfile`, instead of a hardcoded `3.11`. The PR only touched `.github/workflows/build-and-deploy.yml`. It merged to `develop` clean, every check green.

He clicked into which jobs actually ran. `Test and build Images` said `skipped`.

The repo's CI gates its build matrix on path diffs: only images under `images/*` that actually changed get built. This PR touched only the workflow file — not a single image directory. The new logic landed on the main branch and had never run a single time.

Alex then ran four more rounds of testing, each one closing in a little tighter on the same conclusion:

**A safety net that's "available" but has never actually fired is indistinguishable from one that doesn't exist. You have to force it to run yourself, and then look at exactly what it catches — and what it doesn't.**

This post walks through how he did that, including two real gaps nobody at the company knew existed until this exercise surfaced them.

What you'll walk away with:

- **"CI is green" and "CI actually ran" are two different claims** — path-based gating can merge code that never once executes.
- **Testing your own safety net against real, organic drift beats inventing a scenario** — but some blind spots don't exist in production yet, and the only way to find them is to go build one yourself.
- **A safety check's own assumption can be its biggest hole** — "abi3 is always safe" sounds like common knowledge. It isn't.

The order below follows how Alex actually discovered things, not the tidier "how you should do this" order — because each thing he hit is the direct reason for the next test.

---

## 1. Who does the green checkmark actually fool

Alex's first instinct was the normal one: PR merged, checks green, move on.

This time he looked one level deeper, at the actual job list:

```
Create Application Version   success
Test and build Images        skipped   ← the new logic lives inside here
Deploy to SIT/STG/PRD        skipped
```

`Test and build Images` is a matrix job containing both new steps: deriving the version from the Dockerfile, and validating the ABI tag on compiled artifacts. It said `skipped`, not `success`.

The reason is simple and easy to miss: the repo's `List modified images` job diffs which `images/*` paths changed. This PR only touched the workflow file — zero image paths changed — so the matrix concluded "nothing to build" and skipped the whole job.

> **The obvious read**: green CI means the change is correct.
> **The read that actually matters**: green CI means the part that ran is correct. Ask which jobs the change actually caused to execute before trusting the light.

| What you see | Looks like | What it actually is |
|---|---|---|
| All PR checks green | New logic verified | The job containing the new logic was path-filtered out — it never ran |
| `skipped` | Some flavor of "passed" | Never executed, not even once |
| Merged to `develop` | Code is live | Code is on the main branch, but its trigger condition has never fired |

> Path filtering exists to save CI time, and there's nothing wrong with that design on its own. The mistake is treating "this job is allowed to be skipped" and "this change doesn't need verification" as the same statement — one is a trigger rule, the other is a claim about correctness, and they have nothing to do with each other.

---

## 2. Forcing it to actually run: a throwaway touch commit

Once he knew it had never run, Alex didn't reach for a test framework or try to mock GitHub Actions' behavior — that tests what you *think* it does, not what it actually does.

Instead: a new branch, a version-only touch commit on one real image's `pyproject.toml` (`0.1.0` → `0.1.1`, zero functional change), just to make `List modified images` think that image changed, and force its matrix job to actually run.

```bash
git checkout -b verify-ci-python-version-resolution develop
# fs__qcc__core depends on paramiko/cryptography — one of the few images
# in this repo that actually produces compiled extensions. Picking it
# wasn't arbitrary: pick a pure-Python image instead and the new logic
# has nothing to check.
sed -i '' 's/version = "0.1.0"/version = "0.1.1"/' images/fs__qcc__core/pyproject.toml
git commit -am "touch fs__qcc__core to exercise new CI python-version resolution"
git push
```

Which image to pick is where the real judgment call lives — pick wrong (say, a boto3-only image with no compiled dependencies at all) and the job runs, but the new logic has nothing to validate. Another green light that proved nothing.

This time, the moment it actually ran, CI turned red:

```
Building fs__qcc__core against Python 3.11 (derived from Dockerfile base image)
...
ERROR: Package 'edr-common-python' requires a different Python: 3.10.20 not in '<3.12,>=3.11'
```

Nothing here was staged. `fs__qcc__core`'s `Dockerfile` really was `FROM python:3.10-slim` at the time, and its dependency `edr-common-python` — an unpinned internal package tracking git HEAD directly — now required `>=3.11,<3.12`. This drift already existed in the repo. The first time the new logic actually executed, it caught a real, organically-occurring problem with a clear, actionable error message.

> **One-line takeaway**: the best material for testing "does this catch drift" code isn't a scenario you invent — it's whatever's already sitting in your repo, quietly not yet stepped on.

---

## 3. A second real test: pushing the boundary the other direction

The first test caught "version too old." Alex wanted to know about the other direction — if someone bumped a Dockerfile's Python version for a routine security patch, would the new logic catch a problem there too?

He picked another real image depending on `edr-common-python`, `dm_oru`, and changed exactly one line of its Dockerfile — `pyproject.toml` untouched:

```diff
- FROM python:3.11-slim
+ FROM python:3.12-slim
```

Result:

```
Building dm_oru against Python 3.12 (derived from Dockerfile base image)
...
ERROR: Package 'edr-common-python' requires a different Python: 3.12.13 not in '<3.12,>=3.11'
```

The version resolution itself worked exactly right — Dockerfile said 3.12, CI actually built with 3.12. What blocked the upgrade was `edr-common-python`'s own version ceiling.

The real value of this test is the comparison: **how would the old, hardcoded CI have handled this same upgrade?** It wouldn't — regardless of whether the Dockerfile said 3.10, 3.11, or 3.12, the old CI always built and tested with 3.11. A real, meaningful base-image bump would have shipped green, with nobody ever having verified the dependency graph actually works under 3.12. For the first time, the new logic put a real gate in front of an action ("bump the base image") that had never actually been checked before.

| | Old CI (hardcoded 3.11) | New CI (derived from Dockerfile) |
|---|---|---|
| Dockerfile bumped to 3.12 | Still builds with 3.11 — the upgrade itself is **never validated** | Actually builds with 3.12, hits `edr-common-python`'s ceiling immediately |
| When you find out | Possibly a `ModuleNotFoundError` in production | At PR time, with an error that points straight at the dependency |

---

## 4. Attacking a pattern that doesn't exist yet: the multi-stage Dockerfile

The first two tests used real, existing repo state. For the third, Alex deliberately went looking for a pattern **no image in the repo currently uses** — a multi-stage Dockerfile — because it's an entirely ordinary Docker idiom, and someone will eventually reach for it. The version-resolution script looks like this:

```bash
version="$(sed -nE 's|^FROM[[:space:]]+python:([0-9]+\.[0-9]+).*|\1|p' Dockerfile | head -1)"
```

`head -1` — take only the **first** `FROM python:` line in the file. Fine for a single-stage Dockerfile, since there's only one. For a multi-stage one:

```dockerfile
FROM python:3.11-slim AS builder   # ← first FROM — head -1 grabs this

FROM python:3.10-slim              # ← the last one is what actually ships
RUN adduser --system --home /edr-python --group edr-python
...
```

Alex pushed this to the same test branch. CI built, tested, and packaged with 3.11 — then the extension-validation step compared "expected ABI: cpython-311" against the actual artifact, which genuinely **was** compiled with 3.11. Both sides matched perfectly.

**Green.**

But the green was false. The image that would actually ship is based on `python:3.10-slim`, not 3.11. The "expected value" the check compares against and the artifact it's comparing come from **the same wrong derivation** — they can never disagree with each other, because they're the same bug wearing two hats.

> **Symmetry breaking**: this check looks like two independent signals cross-validating each other (the derived version vs. the actual compiled artifact), but it's really one bug projected twice. Any "self-verifying" check deserves the question: are these two signals actually independent, or do they share the same upstream assumption?

This is a risk the repo has zero exposure to today — all 24 images are single-stage. But "the new logic hasn't been bitten by this pattern yet" and "the new logic can't be bitten by this pattern" are two different sentences. The first is luck. The second is an engineering guarantee.

---

## 5. The abi3 landmine: a green-light check that doesn't know it's wrong

By this point Alex was done pushing test scenarios through GitHub Actions — the multi-stage case had already shown that CI round-trips were getting expensive, and a lot of these assumptions could be checked faster and cleaner locally. He opened Docker on his laptop and reproduced a deeper problem in a few minutes.

The new validation logic carries this comment:

```
Version-tagged .so files must carry the target ABI tag; abi3 (.abi3.so)
and pure-Python files are portable and skipped.
```

`abi3` is CPython's stable ABI subset — an extension that only touches that subset compiles once and works across every 3.x minor version, no per-version wheels needed. The assumption baked into that comment: **abi3 files are always safe, skip them.**

That assumption sounds completely reasonable. Alex decided to test it directly:

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
RUN pip install --target /build/pkgs cryptography paramiko

FROM python:3.10-slim
COPY --from=builder /build/pkgs /app/pkgs
ENV PYTHONPATH=/app/pkgs
CMD ["python", "-c", "import paramiko"]
```

```
$ docker build -t py-drift-test . && docker run --rm py-drift-test

ImportError: /app/pkgs/cryptography/hazmat/bindings/_rust.abi3.so: undefined symbol: PyType_GetName
```

The file that crashed is exactly the one judged "always safe." Why: the C API symbol `PyType_GetName` was only added to the stable ABI in Python **3.11**. `cryptography`'s Rust bindings use it, which means this particular abi3 wheel's real minimum runnable version is 3.11 — an older interpreter breaks on it regardless of whether the filename says `abi3`.

**abi3 was never a guarantee of "works everywhere." It's a guarantee of "works from its build floor onward."** It's forward compatibility, not symmetric portability. Collapsing "safe across minor versions" into "skip anything with abi3 in the filename" is itself the hole.

| File | How the check treats it | What's actually true |
|---|---|---|
| `_cffi_backend.cpython-311-*.so` | Scanned, flagged if the tag doesn't match | Handled correctly |
| `_rust.abi3.so` (cryptography) | Skipped outright, assumed safe | **Wrong** — this is exactly what crashed |

### Correcting an obvious-sounding instinct

At this point it's tempting to think: "just bump the Docker base image to 3.12 everywhere and this can't happen."

It doesn't. The root cause here is "the running version is older than the compiled artifact's minimum floor" (3.10 < the 3.11 floor), not "the version is old" as an abstract fact — a final stage on 3.11 or 3.12 both work fine against this exact wheel.

And "bump to 3.12" is already a dead end in this repo — section 3's `dm_oru` test already proved that any image depending on `edr-common-python` hits its own `<3.12` ceiling the moment you try, with the identical error. Upgrading the version here isn't fixing this problem, it's trading it for a different guaranteed failure.

The actual fix is singular: **build-time and runtime Python must always be the same version — no drift, period.** That's the same conclusion the last post landed on, reproven here through a completely different failure mode.

---

## Putting the five rounds together

| Round | What it tests | Material used | Result |
|---|---|---|---|
| 1 | Did the new logic run at all | The repo's real path-filtering rule | Never ran, not once |
| 2 | Force real execution — does it catch real drift | Repo's actual 3.10 vs `edr-common-python`'s requirement | Caught it, clean actionable error |
| 3 | Does it also block an upgrade going the other way | A real one-line Dockerfile change (3.11→3.12) | Caught it — the old CI never could have |
| 4 | Structural blind spot in the resolution logic itself | A hand-built multi-stage Dockerfile (doesn't exist in the repo) | False green — the check and the build share the same wrong assumption |
| 5 | Whether the check's own assumption holds | Local Docker repro, a real `ImportError` | False green — "abi3 is inherently safe" is itself wrong |

The first two rounds test "can this code be verified against something real." The last two test "does this code's own assumption actually hold." You need both before you can say a safety net has genuinely been checked — not "it merged, so it counts," but "I forced it to run, forced it to face real drift, and forced it to face a scenario it didn't even know it could lose."

## Do this today

1. Before merging any PR that only touches CI configuration and no application code, check which jobs actually executed — `skipped` and `success` look almost identical and mean completely different things.
2. If your CI gates a build matrix on path filters, consider pairing any "workflow-logic-only" PR with a dedicated, throwaway touch commit that forces at least one real branch to exercise the new logic before you merge.
3. When reviewing any check that skips a category of file or a naming pattern, treat this as a mandatory question: is the condition that triggers the skip actually one-directional, or only true within a narrower range than it sounds? "abi3" sounds like "works everywhere" — it actually means "works from some version, forward."

---

*A green checkmark was never the finish line. It's a question: who put that mark there, what did it actually verify, and under what conditions did it get to say yes?*
