---
title: Why "Make the Red Go Away" Is a Dangerous Objective Function
header:
    image: /assets/images/hd_git.png
date: 2026-10-15
tags:
 - devops
 - security
 - git
 - engineering-culture
permalink: /blogs/tech/en/danger-of-making-red-go-away
lang: en
layout: single
category: tech
---
> "The map is not the territory." — Alfred Korzybski

*From "just get the commit through" to "figure out why it won't go through" — and the live OAuth key sitting in the gap between them.*

```
Check for added large files..............................................Passed
Detect hardcoded secrets.................................................
```

A `git commit` hung here, the cursor frozen. No error message appeared, no exit code was returned; it just stalled at the `gitleaks` step. 

The immediate reflex for most engineers is: *"The hook is stuck, let me get past it."* 

This post is about why that reflex is a trap. The line `Detect hardcoded secrets...` is a **map**. The territory is a runaway process pinning the machine at load 40 and a 40MB staged diff hiding 14 real Google OAuth secrets. If you optimize your workflow for "make the red go away," you will succeed in your objective while failing your actual job: you will get both failures in sequence—first a misdiagnosis, then a security leak.

By the end of this post, you will have a mental model for distinguishing "stuck" from "failed" states and a strategy for handling high-density security alerts without creating security debt.

## 1. "Stuck" Is Not "Failed": First Tell Which Red You're Looking At

When a pre-commit hook hangs, the frozen cursor forks into two distinct diagnostic roads. Identifying which one you are on is the difference between fixing a bug and fixing a system.

- **Road A**: The hook is rejecting the commit (non-zero exit). That is a *failed* state. The hook is doing its job; you need to read the error and fix the code.
- **Road B**: The hook hasn't produced a result at all; a process is spinning. That is a *stuck* state. The problem may not be the hook's logic, but the environment's resources.

I nearly took Road A immediately, reaching for the `gitleaks` config to "stop the hang." One command stopped me:

```bash
ps aux | grep gitleaks
# 35958 ... gitleaks git --config .gitleaks.toml --redact -v   # 91 min of CPU
uptime
# load averages: 22.80 39.96 33.70
```

The machine was being flattened by a `gitleaks git` process—specifically one running **without** the `--staged` flag—scanning the *entire* git history (40MB+). The pre-commit hook is intended to run `gitleaks git --pre-commit --staged`, which should only take tens of milliseconds. The commit wasn't rejected by the hook; it was starved of CPU by a background job I had fat-fingered into existence earlier.

| State | Stuck | Failed |
|---|---|---|
| **Signal** | No output, frozen cursor, fans screaming | A clear exit code, error text |
| **Where to look** | `ps` / `uptime` / `top` — system resources | The hook's output, its config, the scanned content |
| **Classic wrong move** | Edit the hook config "so it stops hanging" | Throw hardware at it "so it stops being slow" |
| **Right move** | Find and kill the process actually eating resources | Read the error, fix *that* |

> The **shape** of the red tells you which illness it is. Silent red and red-with-an-exit-code are two different diagnostic paths; take the wrong one and you'll perform correct surgery on the wrong organ.

## 2. 129 Alerts Is Not a Blob of Noise — It's Three Things Mixed Together

Once the runaway process was killed and the load fell, the real `--staged` scan finally executed:

```
scanned ~40.49 MB (40.49 MB) in 1m1.7s
WRN leaks found: 129
```

When a scanner returns a number like 129, the strong, wrong intuition is: *"That many must be false positives; just allowlist the lot to get back to work."*

However, bucketing the results by file reveals a different picture:

| Bucket | Count | What matched | Verdict |
|---|---|---|---|
| Noise | ~100 | Scraped third-party web pages `raw_html/*.html`, notes, a UUID in a 2023 log sample | Not my secrets — safe to exempt |
| Browser session JWTs | 15 | `*_auth_state.json`, `*_session.json` (Jira / Azure DevOps / GitHub login state) | Real tokens |
| **Real credentials** | **14** | `client_secret_*.json`, `token.json`, `credentials*.json` — **Google OAuth client secrets and tokens** | Real keys |

The scanner was right. Buried in a hundred lines of web-page noise, it precisely caught 14 of my own OAuth secrets—and those files were `M` (modified, already tracked), meaning they had been in the repo for a while. I was just renewing their lease.

That is what makes 129 dangerous: it is large enough to trigger the "allowlist everything" reflex, and the cost of that silence is waving through the real keys mixed into the noise. High alert density is not a reason to skip per-line review; it is the opposite. **The bigger the diff and the denser the alerts, the higher the payoff of bucketing them**, because that is exactly where a real key hides best.

> Optimize the scanner's output as a boolean (pass/fail) and you throw away its real value: it's a **classifier**, not a gate.

## 3. Allowlist for Noise, Untrack for Keys

Once you admit the three buckets are different things, the handling must fork. Using one blunt instrument for all of them either leaks data or deletes source code you intended to keep:

```toml
# .gitleaks.toml — exempt only the VERIFIED-noise paths
'''(^|/)raw_html/.*\.html$'''           # scraped third-party pages
'''(^|/)web_scrawl_scratch/.*\.html$'''
'''Meta System Design Knowledge.*\.txt$'''
'''(^|/)ai/unifyxp/support/fixlog_.*\.py$'''  # scripts embedding 2023 log samples
```

```gitignore
# .gitignore — real credentials: never tracked again
*_auth_state.json
*_session.json
client_secret*.json
credentials*.json
token.json
token-*.json
```

```bash
# real credentials: stop tracking, keep the file on disk
git rm --cached <the 17 credential/session files>
```

The shortcut you must **not** take is adding those `client_secret_*.json` paths to the `.gitleaks.toml` allowlist. CI goes green instantly and the commit sails through—but the price is committing live OAuth keys into a public repo's history, over and over. Green will lie to you that it's fine, while in the territory, the keys are walking out the door.

| | Lazy fix | Right fix |
|---|---|---|
| Noise (pages/notes) | Allowlist the path ✅ | Allowlist the path ✅ |
| Real credential (OAuth/token) | Allowlist the path ❌ (commits it) | `git rm --cached` + `.gitignore` |
| Success metric | Did CI go green? | Will a real key enter the *next* commit? |

Re-scan: `no leaks found`. This green is the real one.

## 4. `git rm --cached` ≠ Purging History: There's a Layer After Green

One point that lulls people into relaxing too early: `git rm --cached` + `.gitignore` only fixes the **future**—it removes the files from the index so they are untracked from the next commit onward. But the *old versions* of those 14 OAuth secrets **are still sitting in the history commits**.

Anyone who has cloned the repo already has them. Therefore, the real finish involves two steps that have nothing to do with simply getting the commit through:

1. **Rotate** — revoke and reissue those Google OAuth client secrets / tokens. Once they've been in public history, treat them as leaked.
2. **Purge history** — use `git filter-repo` to scrub the files from every historical commit. This rewrites all commit hashes and requires a force-push, which is high-risk—back up first.

This is the inverse of "code archaeology": take the lazy green today, and in three months nobody remembers there's a key buried in the history.

> `rm --cached` keeps new keys from coming in the door; it does not escort out the ones already inside.

## Bonus: A Fourth Red, Same Disease

When the commit actually ran, **another** hook blocked it—`check-yaml`, which had nothing to do with gitleaks. Two causes: a batch of multi-document k8s YAMLs (`---`-separated, valid, but `check-yaml` rejects them by default), plus one genuine syntax error:

```yaml
# in a swagger file
  title:XYX Pricing Service   # missing space after title: — the whole doc fails to parse
```

The "make the red disappear" lazy fix here is `git commit --no-verify`—one flag to skip every hook. It passes, and it drags that broken YAML in with it. The right fix is two real ones: give `check-yaml` `--allow-multiple-documents` (multi-doc *is* valid), and put the space back in `title: XYX`. Same disease, fourth appearance: **green isn't the goal, it's the goal's shadow.**

## 5. Rebase Conflicts: The Red That Most Looks Like "Did I Run the Wrong Command?"

The commit finally landed. Then `git pull --rebase` to sync with the remote—and it stopped, spitting out `CONFLICT` on 4 files. The most natural thought in that instant: **"Did I use the wrong command?"**

No. The command was right. **A rebase conflict is not an error**—it's git telling you, honestly, that your commit and the remote's newer commits edited the same region, and it won't pick for you, so it stops and asks.

| The naive read | The seasoned read |
|---|---|
| "It says CONFLICT, I botched the rebase" | A rebase stops at overlapping edits by design — that's the feature, not a fault |
| Panic, `git rebase --abort` and back out | First look at *what the conflict is*, then decide abort vs. resolve |

The real root was one step earlier: **a single `git add -A` swept all 3487 working-tree files into one commit**, many of them *stale versions*, while the remote's recent commits had moved those same files forward. Old version collides with new version; rebase has to pick. And not one of those 4 conflicts came from the actual security fix—they were all dragged in by the giant batch.

The "make the red disappear" lazy fixes here are three, each worse than the last: `git rebase --abort` (throw away the sync), `--skip` (silently drop your own commit), or `push --force` (bulldoze someone else's new work with your stale copy). The right move is to read the two sides—in a rebase, `ours` is the new base you're landing onto (the remote), `theirs` is the commit being replayed (your stale copy)—take the side that loses no work per file, set aside anything real, and `--continue`.

> A one-shot `git add -A` isn't saving effort—it's deferring "I didn't think about what I'm committing" to rebase time, with interest.

## Four Reds, Four Forks

| The red | Lazy fix (make it vanish) | Right fix (understand why) | Cost gap |
|---|---|---|---|
| Hung commit | Edit gitleaks config "to stop the hang" | `ps`/`uptime`, find and kill the runaway process | Surgery on the wrong tool |
| 129 secret alerts | Allowlist the lot | Bucket them: exempt noise, untrack keys | 14 OAuth keys pushed to a public repo |
| check-yaml failure | `--no-verify` to skip | `--allow-multiple-documents` + fix the typo | Broken YAML into main |
| rebase conflict | `--abort` / `--skip` / `--force` | Read ours/theirs, take the safe side per file, `--continue` | Lose your work or someone else's |

Four lines of red, four times the same temptation: set the objective function to "turn it green." And every time, the fastest path to green was exactly the worst engineering decision available.

## What You Can Do Today

1. Run `gitleaks git --pre-commit --staged -v` on your own repo and bucket the results **by file**—don't read the total. The total is there to scare you; the buckets are there to decide with.
2. Hunt for tracked credential artifacts: `git ls-files | grep -iE 'client_secret|credentials|token.*\.json|_auth_state|_session\.json'`. For each hit, `git rm --cached` and add it to `.gitignore`.
3. If step 2 found anything, it's almost certainly in history already: **rotate every matching key**, then decide whether to `git filter-repo` the history.
4. Add `args: ['--allow-multiple-documents']` to your pre-commit `check-yaml` if your repo has k8s manifests—so nobody reaches for `--no-verify` and bypasses the whole security chain to get around it.
5. Make "is this red *stuck* or *failed*?" the first step of your debugging, before you edit any config on a hunch.
6. Drop the reflex `git add -A` / `git add .`: stage by topic, and `git pull --rebase` to land on the latest tip *before* committing—most rebase conflicts are "stale vs. new" and vanish at the source.


*CI going green was never your goal—it's just the shadow your real goal casts. Tune against the shadow, and some late night you'll push a key that should have been revoked straight into history the whole world can read.*


--- 

## Elevation

**The Shape of the Red**

In production systems, error signals are often overloaded. This principle states that the specific metadata of a failure (the "shape") determines the diagnostic path, and switching paths prematurely is the primary cause of incorrect remediation.

- **Mechanism**: Diagnostic path differentiation. A "stuck" state (resource exhaustion) and a "failed" state (logic rejection) share the same visual output (a non-moving cursor/red line) but require opposite actions (kill processes vs. fix code). 
- **Limit**: This only applies when the output is ambiguous. If the error message is explicit (e.g., a 403 Forbidden), the shape is already defined, and the diagnostic path is singular.
- **Transfer**: When a tool hangs or fails unexpectedly, ask yourself: *"Is the tool rejecting my input, or is the environment failing to execute the tool?"* If it's the latter, look at the system resources before you touch the configuration.",
