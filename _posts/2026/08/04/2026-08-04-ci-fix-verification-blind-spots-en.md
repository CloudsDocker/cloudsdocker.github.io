---
title: "The CI Check That Never Ran Once Gave Us a Fake Green Checkmark"
header:
    image: /assets/images/hd_containers.png
date: 2026-08-04
tags:
 - python
 - docker
 - ci-cd
 - github-actions
 - testing
permalink: /blogs/tech/en/ci-fix-verification-blind-spots
layout: single
category: tech
---

> "The first principle is that you must not fool yourself — and you are the easiest person to fool." — Richard Feynman

---

The batch job died in the middle of the night.

Whoever was on call got paged awake to one flat, uninformative line in the logs:

```
ModuleNotFoundError: No module named '_cffi_backend'
```

This job had been running fine for ages. Nothing had changed tonight — or so it seemed. The first instinct is always the same: a missing dependency. Except `cffi` was sitting right there in the lockfile. It was sitting right there in the image's `site-packages`, too. The package was, unambiguously, installed.

The problem was never "installed or not." It was that **the Python that installed it, and the Python that was trying to run it, were not the same Python.** CI had compiled and packaged this thing under 3.11; the artifact got dropped into a container whose base image was 3.10. A 3.10 interpreter scanning for native extensions only recognizes a short, specific list of filename suffixes — and `-311-` isn't one of them. So it doesn't fail to load the file. It **doesn't see the file at all.** Even the error message can't tell you which is true — it just shrugs and says "missing, or built for a different version."

It took Alex half a day to trace that chain all the way down, and two more to ship the fix: stop hardcoding the Python version in CI, and derive it instead from each image's own `Dockerfile` — so build and runtime are permanently locked to the same number, instead of relying on some engineer remembering "oh right, these two things have to match."

PR merged. CI green across the board. He leaned back, let out a breath, and was one click away from closing the ticket and moving to the next one — when a thought floated up, weightless, and refused to leave:

> "What does this green checkmark actually prove?"

He'd find out, eventually, that the honest answer was: almost nothing.

## The 30-second version

That PR touched exactly one file — `.github/workflows/build-and-deploy.yml`. He went and checked which jobs had actually run. `Test and build Images` sat there, quietly, saying `skipped`.

The repo's CI gates its build matrix on path diffs: only images under `images/*` that actually changed get pulled into the build. This PR only touched the workflow file, not a single image directory. The new logic had landed, in full, on the main branch — and had never once been executed.

Alex ran four more rounds of testing after that, each one meaner than the last, each one circling closer to the same sentence:

**A safety net that's "available" but has never actually fired is indistinguishable from one that doesn't exist. You have to force it to run yourself, and then stand there and watch exactly what it catches — and what slips past it.**

This is the story of those five rounds — including the two real gaps nobody on the team knew existed until this exercise dragged them into the light. What you'll walk away with:

- **"CI is green" and "CI actually ran" are two different claims** — path-based gating can merge code that never once executes.
- **Testing your own safety net against drift that's already sitting in your repo beats inventing a scenario** — but some blind spots haven't happened yet, and the only way to find them is to go build one with your own hands.
- **A safety check's own assumption can be its biggest hole** — "abi3 is always safe" sounds like received wisdom. Dig, and it turns out to be wrong.

What follows is the order Alex actually discovered things in, not the tidy "how you should do this" order — because every hole he fell into is the direct reason for the next test.

---

## 1. Who does the green checkmark actually fool

PR merged, checks green — the normal reflex is to move on to the next thing.

This time he looked one level deeper, at the actual job list:

```
Create Application Version   success
Test and build Images        skipped   ← the new logic lives inside here
Deploy to SIT/STG/PRD        skipped
```

`Test and build Images` is a matrix job carrying both new steps: deriving the version from the Dockerfile, and validating the ABI tag on compiled artifacts. It said `skipped`. Not `success`. Two words that look almost identical and mean entirely different things.

The reason is simple enough to walk right past: the repo's `List modified images` job diffs which `images/*` paths changed. This PR touched only the workflow file — zero image paths moved — so the matrix concluded "nothing to build here" and skipped the whole job.

> **The obvious read**: green CI means the change is correct.
> **The read that actually matters**: green CI means the part that ran is correct. Ask which jobs the change actually caused to execute before you let yourself trust the light.

| What you see | Looks like | What it actually is |
|---|---|---|
| All PR checks green | New logic verified | The job containing the new logic was path-filtered out — it never ran |
| `skipped` | Some flavor of "passed" | Never executed, not even once |
| Merged to `develop` | Code is live | Code is on the main branch, but its trigger condition has never once fired |

> Path filtering exists to save CI time, and there's nothing wrong with that design on its own terms. The mistake is quietly conflating "this job is allowed to be skipped" with "this change doesn't need verification" — one is a trigger rule, the other is a claim about correctness, and the two have nothing to do with each other.

---

## 2. Forcing it to actually run: a throwaway touch commit

Once he knew the thing had never run, Alex didn't reach for a testing framework, and he didn't try to mock GitHub Actions' behavior in isolation — that tests what you *think* it does, not what it actually does. Nobody cares what you think.

His approach was blunter: a new branch, a version-only touch commit on one real image's `pyproject.toml` (`0.1.0` → `0.1.1`, zero functional change), just enough to convince `List modified images` that this image had changed, and force its matrix job onto the track for real.

```bash
git checkout -b verify-ci-python-version-resolution develop
# sftp-ingest-core depends on paramiko/cryptography — one of the few images
# in this repo that actually produces compiled extensions. Picking it
# wasn't arbitrary: pick a pure-Python image instead and the new logic
# has nothing to check.
sed -i '' 's/version = "0.1.0"/version = "0.1.1"/' images/sftp-ingest-core/pyproject.toml
git commit -am "touch sftp-ingest-core to exercise new CI python-version resolution"
git push
```

Which image to pick is where the actual judgment lives — pick wrong (say, a boto3-only image with no compiled dependencies at all) and the job runs, but the new logic has nothing to validate. Another green light that proved absolutely nothing.

This time, the second it actually ran, CI turned on a dime and went red:

```
Building sftp-ingest-core against Python 3.11 (derived from Dockerfile base image)
...
ERROR: Package 'platform-shared-lib' requires a different Python: 3.10.20 not in '<3.12,>=3.11'
```

Not a word of this was staged. `sftp-ingest-core`'s `Dockerfile` really was `FROM python:3.10-slim` at the time, and its dependency `platform-shared-lib` — an unpinned internal package tracking git HEAD directly — now required `>=3.11,<3.12`. This drift had been sitting quietly in the repo the whole time. The first time the new logic actually executed, on its very first breath, it caught a real, organically-occurring problem, with an error message that pointed straight at the fix.

> **One-line takeaway**: the best material for testing "does this catch drift" code was never something you invent. It's whatever's already lying in your repo, waiting patiently for someone to step on it.

---

## 3. A second real test: pushing the boundary the other way

The first test caught "version too old." Alex wanted to know about the opposite direction — if someone bumped a Dockerfile's Python version for a routine security patch, would the new logic catch a problem there, too?

He picked another real image depending on `platform-shared-lib`, `report-refresh`, and changed exactly one line of its Dockerfile — `pyproject.toml` left completely alone:

```diff
- FROM python:3.11-slim
+ FROM python:3.12-slim
```

Result:

```
Building report-refresh against Python 3.12 (derived from Dockerfile base image)
...
ERROR: Package 'platform-shared-lib' requires a different Python: 3.12.13 not in '<3.12,>=3.11'
```

The version resolution itself worked exactly as designed — Dockerfile said 3.12, CI actually built with 3.12. What stopped the upgrade cold was `platform-shared-lib`'s own version ceiling.

The real payoff of this test is the comparison it invites: **how would the old, hardcoded CI have handled this exact same upgrade?** It wouldn't have. Regardless of whether the Dockerfile said 3.10, 3.11, or 3.12, the old CI always built and tested with 3.11, full stop. A real, consequential base-image bump would have shipped green, with nobody having ever verified the dependency graph even survives under 3.12. For the first time, the new logic put an actual gate in front of an action — "bump the base image" — that had never once been checked.

| | Old CI (hardcoded 3.11) | New CI (derived from Dockerfile) |
|---|---|---|
| Dockerfile bumped to 3.12 | Still builds with 3.11 — the upgrade itself is **never validated** | Actually builds with 3.12, hits `platform-shared-lib`'s ceiling immediately |
| When you find out | Possibly a `ModuleNotFoundError` in production | At PR time, with an error that points straight at the dependency |

---

## 4. Attacking a pattern that doesn't exist yet: the multi-stage Dockerfile

The first two tests leaned on real, already-existing repo state. For the third, Alex went on the offensive — hunting for a pattern **not a single image in the repo currently uses**: the multi-stage Dockerfile. It's an entirely ordinary Docker idiom. Nobody's using it today doesn't mean nobody will tomorrow. And the version-resolution script looked like this:

```bash
version="$(sed -nE 's|^FROM[[:space:]]+python:([0-9]+\.[0-9]+).*|\1|p' Dockerfile | head -1)"
```

`head -1` — take only the **first** `FROM python:` line in the file. Fine, in a single-stage Dockerfile, where there's only one. In a multi-stage one:

```dockerfile
FROM python:3.11-slim AS builder   # ← first FROM — head -1 grabs this

FROM python:3.10-slim              # ← the last one is what actually ships
RUN adduser --system --home /svc-python --group svc-python
...
```

Alex pushed this to the same test branch and watched CI walk, step by step, straight into the trap: build with 3.11, test with 3.11, package with 3.11 — then the extension-validation step compared "expected ABI: cpython-311" against the actual artifact, which genuinely **was** compiled with 3.11. The two sides matched perfectly.

**Green.**

Clean, tidy, and false. The image that would actually ship is based on `python:3.10-slim`, not 3.11. The "expected value" the check compares against, and the artifact it's comparing, come from **the exact same wrong derivation** — they can never disagree with each other, because they're the same bug looking at itself in two mirrors.

> **Symmetry breaking**: this check looks like two independent signals cross-validating each other — the derived version, the actual compiled artifact — but it's really one bug casting two shadows. Any "self-verifying" check earns the question: are these two signals genuinely independent, or do they share the same upstream assumption underneath?

This is a risk the repo carries zero exposure to today — every image is single-stage. But "the new logic hasn't been bitten by this pattern yet" and "the new logic can't be bitten by this pattern" are two very different sentences. The first one is luck. The second one is an engineering promise.

---

## 5. The abi3 landmine: a green-light check that doesn't know it's wrong

By this point Alex was done pushing test scenarios through GitHub Actions — the multi-stage round had already proven every CI round-trip was burning real time, and a lot of these assumptions could be tested faster and cleaner on his own laptop. He opened Docker locally, and within a few minutes had reproduced something worse.

The new validation logic carries this comment:

```
Version-tagged .so files must carry the target ABI tag; abi3 (.abi3.so)
and pure-Python files are portable and skipped.
```

`abi3` is CPython's stable ABI subset — an extension that stays within that subset compiles once and runs across every 3.x minor version, no per-version wheels required. Buried in that comment is an assumption: **abi3 files are always safe, skip them.**

It sounds reasonable enough that nobody would think to question it. Alex decided to test it with his own hands:

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

The file that crashed is precisely the one judged "always safe." The reason: the C API symbol `PyType_GetName` was only added to the stable ABI in Python **3.11**. `cryptography`'s Rust bindings reach for it, which means this particular abi3 wheel's real minimum runnable version is 3.11 — an older interpreter breaks on it no matter what the filename claims. No negotiation.

**abi3 was never a promise that something works everywhere. It's a promise that it works from its build floor, forward.** It's directional compatibility, not symmetric portability. Collapsing "safe across minor versions" into "skip anything with abi3 in the filename" is itself the hole in the floor.

| File | How the check treats it | What's actually true |
|---|---|---|
| `_cffi_backend.cpython-311-*.so` | Scanned, flagged if the tag doesn't match | Handled correctly |
| `_rust.abi3.so` (cryptography) | Skipped outright, assumed safe | **Wrong** — this is exactly what crashed |

### Correcting an instinct that comes too easily

It's tempting, right about here, to think: "just bump the Docker base image to 3.12 everywhere and this goes away."

It doesn't. The root cause is "the running version is older than the compiled artifact's minimum floor" (3.10 sitting below the 3.11 floor) — not "the version is old" as some abstract sin. A final stage on 3.11 or 3.12 both run this exact wheel just fine.

And "bump to 3.12" is already a dead end in this repo — section 3's `report-refresh` test already proved it: any image depending on `platform-shared-lib` slams into its own `<3.12` ceiling the moment you try, with the identical error message waiting there. Upgrading the version here doesn't fix this problem. It trades it for a different, equally guaranteed one.

There is exactly one real fix: **build-time and runtime Python must always be the same number. No drift, no exceptions.** That's the same conclusion the original production incident forced — proven again here, through a completely different failure mode. Two different cracks, the same wall behind them.

---

## Putting the five rounds together

| Round | What it tests | Material used | Result |
|---|---|---|---|
| 1 | Did the new logic run at all | The repo's real path-filtering rule | Never ran, not once |
| 2 | Force real execution — does it catch real drift | Repo's actual 3.10 vs `platform-shared-lib`'s requirement | Caught it, clean actionable error |
| 3 | Does it also block an upgrade going the other way | A real one-line Dockerfile change (3.11→3.12) | Caught it — the old CI never could have |
| 4 | Structural blind spot in the resolution logic itself | A hand-built multi-stage Dockerfile (doesn't exist in the repo) | False green — the check and the build share the same wrong assumption |
| 5 | Whether the check's own assumption holds | Local Docker repro, a real `ImportError` | False green — "abi3 is inherently safe" is itself wrong |

The first two rounds ask whether this code survives contact with the real world. The last two ask whether the assumption this code believes in survives contact with itself. You need both before you get to say a safety net has actually been checked — not "it merged, so it counts," but "I forced it to run, forced it to face real drift, and forced it to face a scenario it didn't even know it could lose."

## Do this today

1. Before merging any PR that only touches CI configuration and no application code, check which jobs actually executed — `skipped` and `success` look almost identical and mean completely different things.
2. If your CI gates a build matrix on path filters, pair any "workflow-logic-only" PR with a dedicated, throwaway touch commit that forces at least one real branch to exercise the new logic before you merge.
3. When reviewing any check that skips a category of file or a naming pattern, make this the mandatory question: is the condition that triggers the skip actually one-directional, or only true within a narrower range than it sounds? "abi3" sounds like "works everywhere." It actually means "works from some version, forward."

---

*A green checkmark was never the finish line. It's a question, hanging there, waiting for you to answer: who put that mark there, what did it actually verify, and under what conditions was it even allowed to say yes?*
