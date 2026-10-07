---
title: 'Unmasking the IDNA Phantom: The Fat Skills Needed to Debug Pipenv Two-Phase Locks'
header:
    image: /assets/images/bg_raw/BingWallpaper (9).jpg
date: 2026-10-07
tags:
 - pipenv
 - python
 - debugging
 - dependency-resolution
permalink: /blogs/tech/en/debug-pipenv-two-phase-locks-idna
lang: en
layout: single
category: tech
---
# Unmasking the IDNA Phantom: The Fat Skills Needed to Debug Pipenv Two-Phase Locks

*When pip and pipenv disagree on the exact same dependency set, the bug isn't in your math—it's in the resolution engine.*

```text
✘ Locking Failed!
ERROR: ResolutionImpossible
The conflict is caused by:
    The user requested idna==3.6
```

When `pipenv lock` throws this, the instinct is to downgrade or upgrade the accused package. I chased this accusation everywhere. I aligned the Python interpreter version. I upgraded a yanked package sitting next to it. The error did not budge.

Then I handed the exact same dependency set to `pip install --dry-run`, and it resolved on the first try.

Two tools, identical input, entirely different verdicts. The package `pipenv` fingered as the culprit was innocent. By the end of this post, you will see exactly why `pipenv` fails where `pip` succeeds, and how to read the hidden two-phase lock that actually triggers this error.

## The crime scene

Here are the key lines of the repository's `Pipfile`:

```toml
[dev-packages]
requests = "2.32.0"
idna = "3.6"

[requires]
python_version = "3.10"
```

And the output of `pipenv lock`, trimmed of its noisy internal Python traceback:

```text
Locking dependencies...
Resolving dependencies...
✔ Success!
Locking dependencies...
Resolving dependencies...
✘ Locking Failed!
ERROR: ResolutionImpossible
The conflict is caused by:
    The user requested idna==3.6
```

## Falsifying the red herrings

I had two hypotheses that looked completely viable. Both were wrong.

**Red herring 1: The interpreter mismatch.** The virtual environment was built on system Python 3.12, while the `Pipfile` pinned 3.10. `pipenv` warned about this explicitly. I rebuilt the environment under a `docker python:3.10-slim` container. The warning vanished, but the `idna` error remained.

**Red herring 2: The yanked package.** A line flickered past in the logs: `WARNING: The candidate selected ... is a yanked version: 'requests' (2.32.0)`. Under PEP 592, a maintainer can flag a version as yanked to prevent auto-selection, though it still installs if pinned exactly. `requests` was yanked due to a CVE-2024-35195 mitigation conflict. I was certain this was it. I bumped `requests` to the non-yanked `2.32.3`. `pipenv` failed anyway.

## The decisive comparison

If the dependency math is truly impossible, no tool should be able to solve it. I handed the same pinned set straight to `pip`:

```bash
pip install --dry-run --index-url <nexus> \
  pysftp python-gnupg cryptography==44.0.1 urllib3==1.26.19 paramiko==3.4.0 \
  botocore aiobotocore boto3 pytest==7.4.0 moto==4.2.14 \
  requests==2.32.3 "idna==3.6" pytest-sftpserver==1.3.0
```

The result: `Would install ... idna-3.6 ... requests-2.32.3`. Success.

That proves `idna==3.6` is fully compatible with the whole set. Since `pip` can solve it and `pipenv` cannot, the difference is strictly in the resolution process.

| Resolver | Passes | State at `[packages]` | State at `[dev-packages]` | Result |
|---|---|---|---|---|
| **pip** | 1 (Combined) | N/A | Sees `>=2.0` and `==3.6` together | Picks `3.6` (Success) |
| **pipenv** | 2 (Sequential) | Locks `idna` to `3.7` | `3.7` meets `3.6` | `ResolutionImpossible` |

## The two-phase lock

Look closely at the `pipenv` output again. Notice the `✔ Success!` followed immediately by `✘ Locking Failed!`. Those are two distinct phases. `pip` never does this.

1. **Phase 1: Lock `[packages]` (default).** The default packages quietly pull `idna` in transitively: `aiobotocore` → `aiohttp` → `yarl` → `idna(>=2.0)`. Because nothing in the default section pins `idna` strictly, `pipenv` locks it to the newest available version: `3.7`. This phase succeeds.
2. **Phase 2: Lock default + `[dev-packages]`.** Now the hard `idna==3.6` from the dev section enters the arena. `pipenv` requires exactly one version per package across all sections. The engine tries to reconcile the `3.7` it just locked with the `3.6` it just discovered. They conflict. The lock fails.

A single command proves this by resolving only the default packages:

```bash
pip install --dry-run --index-url <nexus> \
  pysftp python-gnupg cryptography==44.0.1 urllib3==1.26.19 paramiko==3.4.0 \
  botocore aiobotocore boto3 2>&1 | grep -i idna
```

```text
Collecting idna>=2.0
  Downloading idna-3.7
```

`pip` resolves default and dev requirements in a single pass. It sees `idna>=2.0` and `idna==3.6` simultaneously, picks `3.6` because it satisfies both, and finishes cleanly. `pipenv` traps itself by committing to `3.7` before it ever looks at the dev dependencies.

## The fix and the limit

Relax the pin:

```toml
idna = "3.6"     # Before
idna = ">=3.6"   # After
```

Now Phase 2 can accept Phase 1's choice. Both phases converge on `3.7`, and the lock succeeds.

🩸 **Warning:** This is a security-pin decision, not a mechanical edit.

The intent behind `idna==3.6` was almost certainly to establish a floor for CVE-2024-3651 (an `idna.encode()` DoS vulnerability). Relaxing it to `>=3.6` yields `3.7`, which is strictly safer. But you do not loosen a security pin unilaterally just to turn a PR green. Take it to the repository owner. Transitive dependencies do not respect your dev/prod split, so pin in the section that is actually affected.

## Elevation: A Hypothesis Is Only A Narrative Until Proven

The yanked `requests` package was a perfect narrative. It had a warning, it involved a CVE, and it historically causes resolver divergences. I believed it completely.

**Mechanism:** A hypothesis that perfectly explains a failure is still just a narrative until the fix derived from it actually works. We often stop debugging when the story holds together, rather than when the system proves the story true.

**Limit:** This applies strictly to deterministic failures like dependency locks. For intermittent race conditions, a fix that appears to work might just be masking the symptom or shifting the timing.

> Generalize: What is the cheapest command I can run to prove this highly plausible theory wrong?

## The unseen trigger

This surfaced without a single change to `idna`.

We had just swapped to an internal Nexus PyPI proxy. Public `pypi.org` keeps every old release; a firewalled proxy quarantines some. Changing the index changes the set of available versions. Combine that restricted set with a transitive dependency that always reaches for the newest release, and a dead pin that resolved yesterday becomes unsolvable today.

Understanding how a tool searches is worth more than understanding what it prints. The next time `ResolutionImpossible` names a specific package, do not just move the pin. Ask yourself: is this a real conflict, or did the traversal order just paint the resolver into a corner?
