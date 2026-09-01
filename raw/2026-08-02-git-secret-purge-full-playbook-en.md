---
title: "From git bundle to filter-repo: Anatomy of a Secret-Purge Operation"
date: 2026-08-02
categories: [engineering, git, security]
tags: [git, filter-repo, git-stash, subprocess, secret-purge, devops]
---

One day you discover a secret file sitting somewhere it never should have been, buried in your Git history. What comes next isn't panic — it's a sequence: back up, investigate, cut, and finally harden the tooling that did the cutting. This post walks through that full playbook in four parts.

## Part 1: git bundle — Sealing the Whole Repo Before You Operate

Bottom line up front: this is textbook "leave yourself an escape hatch before doing something destructive to repo history (like `git filter-repo` or `BFG`)."

```bash
W=~/.secret-purge-20260802
git bundle create $W/original-history-backup.bundle --all
chmod 600 $W/original-history-backup.bundle
git bundle verify $W/original-history-backup.bundle
```

### 🎯 The 30-Second Version

`git bundle` packages an entire Git repo (every branch, every tag, every commit object) into a **single file** — essentially a self-contained pack file plus a ref list. It needs no network, no Git server; the `.bundle` file itself can be `clone`d/`fetch`ed from as if it were a remote. Before running something as destructive as `git filter-repo`, doing `git bundle create --all` first is your "if this rewrite goes sideways, I can instantly time-travel back" save point.

### ⚙️ Under the Hood

- **`--all`** is shorthand for `--branches --tags` — every object reachable from `refs/heads/*` and `refs/tags/*` gets packed in, but **stash, reflog, and any dangling commit with no ref pointing at it are excluded.**
- The file format is a plain-text header (listing packed refs, their SHAs, and any prerequisite lines) followed by a standard Git **pack file** — the exact same wire format used when you `git push`.
- `chmod 600` isn't a Git concern, it's defense in depth: if this backup contains the very secret you're trying to purge (likely, since that's why you're making the backup), the backup file itself is now sensitive and needs to be locked down to owner-only.
- `git bundle verify` parses the header, checks whether any prerequisite commits exist, and validates pack-file integrity — a lightweight `git fsck`.

### 🔬 The Interviewer's Follow-Up Chain

**Q: Does `--all` miss anything?**
> Yes — stash (`refs/stash`) and reflog. If a leaked secret only exists in a commit that got overwritten by `amend`/`rebase` (now living only in reflog), this backup won't capture it — though that's arguably fine, unless you specifically want a full forensic snapshot of pre-cleanup state.

**Q: How would you also back up stash and reflog?**
> Either `git bundle create backup.bundle --all $(git rev-list -g --all)`, or the blunt-instrument approach: `tar czf backup.tar.gz .git`, a physical copy of the entire `.git` directory — the only 100% lossless option.

**Q: When does `verify` fail?**
> Typically a missing prerequisite commit on an incremental bundle, or file corruption from a broken transfer — a pack-file checksum mismatch throws `fatal: index-pack failed`.

### 🏗️ How Big Tech Uses This at Scale

Early Android/AOSP offline sync, cross-datacenter migrations, and compliance-heavy audit trails ("here's the pre-cleanup snapshot") in finance — `bundle` is standard practice here, not overkill.

### 💸 The High-Stakes Version

In fintech environments obsessed with audit-chain integrity, backups often need to land in WORM storage or be encrypted at rest, not just protected by file permissions. And critically: once a secret is purged, the underlying credential must be rotated at the source immediately — that matters a hundred times more than whether the Git history is clean.

### 🌉 The Cross-Discipline Lens

"Back up, then operate" is the same logic as drawing blood and typing it before surgery — you're not assuming the operation will fail, you're acknowledging that "irreversible high-risk procedure with no fallback" is itself a design flaw. `git bundle` is your blood bag.

### 🥋 Mic-Drop Summary

**Skipping the bundle backup before rewriting Git history is like a surgeon skipping the blood type check before cutting — it's not confidence, it's the absence of a basic failure plan.**

---

## Part 2: git stash — Digging Up the Hidden Third Parent

`bundle` backs up committed history, but `git stash` may still be hiding sensitive files that were **never committed** at all. This part goes digging for that leftover.

```bash
git stash show -p stash@{0} > tracked.patch
git show --name-only --pretty= stash@{0}^3   # untracked files
git show stash@{0}^3:$f                       # extract actual content
```

### 🎯 The 30-Second Version

A single `git stash -u` (which also saves untracked files) actually creates **up to three commits** under the hood: one for tracked-file changes (parent 2), one for untracked files (parent 3), plus the index state (parent 1) — stitched together into one merge commit. A normal `pop` restores all of it automatically, but if you want to inspect it forensically without restoring, you have to manually `git show` these hidden parents.

### ⚙️ Under the Hood

```
stash@{0}          <- a special merge commit, pointed to by refs/stash
  ├── ^1  = HEAD snapshot
  ├── ^2  = index (staged) changes snapshot
  └── ^3  = untracked file snapshot (only present with -u or -a)
```

`^3` is the key piece — it's not a diff, it's a full, standalone commit. `git show stash@{0}^3:$f` uses `commit:path` syntax to cat raw bytes straight out of the object store, without touching the working directory or the index.

### 🔬 The Interviewer's Follow-Up Chain

**Q: Does `^3` exist if you stashed without `-u`?**
> No. It's only created when you explicitly pass `-u` (untracked) or `-a` (all, including ignored files).

**Q: What's the hidden cost of `stash -u`?**
> It generates a full tree + blob object graph for the untracked files, and these objects are **not swept up by an ordinary `git gc`** because `refs/stash` is a reachable ref — this is often the hidden reason a `.git` directory balloons even though "nothing was committed."

**Q: Does `stash drop` actually delete anything?**
> No. Dropping just moves the `refs/stash` pointer. To truly purge the data you need `git reflog expire --expire=now --all && git gc --prune=now --aggressive` afterward — that's the actual shredder, not just the recycle bin.

### 🏗️ How Big Tech Uses This

Plenty of public secret-leak postmortems follow the same pattern: an engineer stashes a `.env` with real credentials via `stash -u`, later runs `stash clear` assuming it's gone, and a security scanner still pulls the secret out of dangling objects — because no one ever ran `gc --prune=now`.

### 💸 The High-Stakes Version

In regulated fintech codebases, `git stash` is often institutionally discouraged or outright disabled at the tooling level, precisely because it's a state that lives outside commit history and triggers no hooks — a genuine audit blind spot. Many compliance pipelines check `git stash list` is empty in a `pre-push` hook.

### 🌉 The Cross-Discipline Lens

The three-parent stash structure resembles a "hidden chart" in a medical record — the official chart (commit history) only shows what was formally diagnosed and treated, but there's also an unofficial layer of preliminary tests and off-book notes (the untracked files in stash). Auditing only `git log` misses exactly the sensitive data sitting in `refs/stash`.

### 🥋 Mic-Drop Summary

**A `git stash` isn't "never happened" — it's just the evidence moved from page one of the chart to the appendix. A real secret cleanup has to burn the appendix too.**

---

## Part 3: git filter-repo — When the Scalpel Actually Comes Down

The first two steps were drawing blood and taking notes. This is the actual surgery — `--invert-paths` physically strips the secret/backup files out of the entire commit history, while `--replace-text` scrubs leaked strings scattered across other files.

```bash
nohup setsid git filter-repo --force \
  --replace-text $W/replacements.txt \
  --path ufiz/tfn/auto_aws/token_output.txt \
  --path src/main/code/env/mac/.zshrc.bak.20260731-082026 \
  --path src/main/code/env/mac/.zshrc.bak.20260731-082111 \
  --invert-paths \
  > $W/filterrepo.log 2>&1 < /dev/null & disown
```

### 🎯 The 30-Second Version

`git filter-repo` doesn't **edit** history — it **rebuilds** it. It walks every commit, recomputes the tree (dropping specified paths, replacing specified text), then regenerates an entirely new commit chain where every SHA differs from the original.

### ⚙️ Under the Hood

- **Rewriting isn't editing, it's rebuilding the DAG.** A commit object stores a tree SHA plus parent SHA(s), and SHAs are content hashes. Change one commit's content and every descendant's SHA changes too — that's why this class of operation is a one-shot nuclear option, not an incremental edit.
- **`--path X --invert-paths`**: builds a "paths to keep" ruleset, inverts it into "paths to drop," then prunes each commit's tree accordingly. If a commit's tree ends up identical to its parent's after pruning, filter-repo skips the commit entirely (empty-commit pruning).
- **`--replace-text`** scans every blob byte-for-byte, which is far slower than path filtering — exactly why this runs backgrounded with `nohup ... &`.
- **`setsid`** detaches the child process from the controlling terminal into a brand-new session, cutting the signal chain at the root so a dying parent terminal can't take the child down with it. `disown` removes it from bash's job table so the shell's exit doesn't touch it either.

### 🔬 The Interviewer's Follow-Up Chain

**Q: Why does this need to run on a clean clone?**
> Because it force-rewrites every ref — old SHAs become invalid everywhere. Get a path wrong and there's no undo unless you have a bundle backup.

**Q: Do the deleted files linger anywhere?**
> They stay in the *old* `.git/objects`, but are unreachable from the new history. `filter-repo` automatically runs `reflog expire` + `gc --prune=now` when it finishes — this is one place it's meaningfully better than `filter-branch`, which requires manual cleanup.

**Q: Are multiple `--path` flags AND'd or OR'd?**
> OR'd. Each `--path` adds matching paths to the candidate set; multiple flags union together.

**Q: What if the process gets killed mid-run?**
> No permanent corruption. `filter-repo` builds the entire new history in a fresh object store first, then atomically swaps the refs at the end — a mid-run kill almost always leaves the original refs pointing at the old history, though a leftover lock/backup directory needs cleanup before you can re-run it.

### 🏗️ How Big Tech Uses This at Scale

`git filter-branch` is officially flagged deprecated for being slow and dangerously easy to misuse; `filter-repo` is the only tool the Git project itself endorses now, typically an order of magnitude faster. Massive monorepos (Google's Piper, Meta's fbsource) essentially never run a full-history rewrite tool like this at all — their strategy is entirely front-loaded into pre-submit interception instead.

### 💸 The High-Stakes Version

Running `filter-repo` is only step one: every collaborator must be forced to re-clone rather than `pull`; every downstream mirror (CI caches, internal artifact repos, forks) must be swept; and a full operational audit trail needs to be kept. The real backstop is always credential rotation — independent of whether the repo history got cleaned up.

### 🌉 The Cross-Discipline Lens

This is stratigraphic replacement in archaeology — you're not pulling one artifact out of one layer, you're saying "this entire geological cross-section, wherever this mineral shows up, gets swapped, and every layer above it gets its date recalculated."

### 🥋 Mic-Drop Summary

**`git filter-repo` isn't deleting files — it's retelling your repo's entire story with a new causal chain. So before you hit enter, the old story better already be locked in a vault.**

---

## Part 4: subprocess.Popen(start_new_session=True) — Python's Version of Cutting the Cord

This round swapped `setsid git filter-repo & disown` for pure Python: `subprocess.Popen(..., start_new_session=True)`. Same goal, different implementation path.

```python
p = subprocess.Popen([
    'git', 'filter-repo', '--force',
    '--replace-text', replacements_path,
    '--path', 'ufiz/tfn/auto_aws/token_output.txt',
    '--invert-paths',
], cwd=repo_path,
   stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
   start_new_session=True)
```

### 🎯 The 30-Second Version

`start_new_session=True` maps directly to the C library's `setsid()` syscall — the child becomes the leader of a brand-new session, detached from the parent's terminal control group. It's the same effect as the hand-rolled `setsid ... & disown` from the previous step, just expressed as a single argument instead of three commands glued together — fewer moving parts, fewer failure modes.

### ⚙️ Under the Hood

- `setsid()` does three things: the child becomes a new session leader, becomes a new process group leader, and **loses its controlling terminal** — that last part is the whole point, since without a controlling terminal there's no target for the terminal to deliver `SIGHUP` to.
- `stdin=subprocess.DEVNULL` explicitly redirects the child's stdin to `/dev/null`, preventing it from inheriting a terminal fd that might get closed out from under it and trigger an unexpected `EOF`/`SIGPIPE`.
- **The single most important detail**: stdout and stderr both go to the same file object, not `subprocess.PIPE`. With `PIPE`, once the kernel pipe buffer fills up (typically 64KB on Linux) and nobody's reading it, the child process blocks on `write()` — and since this script prints and exits almost immediately, nothing would ever drain that pipe. `filter-repo` would very likely just hang. Writing straight to a file has no such ceiling.

### 🔬 The Interviewer's Follow-Up Chain

**Q: The Python script exits after `sleep(10)` — does the child get killed too?**
> No, that's the entire point of `start_new_session=True` — it severs the terminal signal delivery path at the root.

**Q: Does this code check whether the child actually started successfully?**
> No, and that's a real robustness gap. `Popen()` succeeding only means fork+exec didn't error out — it says nothing about whether the child's logic is actually correct. Production-grade code should check `p.poll()` after the sleep.

**Q: How do you reliably check completion later?**
> While the Python process is still alive, `p.wait()`/`p.poll()` is authoritative. Once the script itself has exited, you're reduced to `pgrep`/`ps -p`, which risks false positives since PIDs get recycled. The more reliable approach is checking the log for a completion marker rather than trusting process existence alone.

**Q: What does wrapping this in Python actually buy you over raw shell?**
> Composability and testability. A `Popen` object supports structured state management, and slotting this into something like an Airflow `PythonOperator` down the line is far more maintainable than piling shell tricks into a `BashOperator`.

### 🏗️ How Big Tech Uses This

The `nohup`/`setsid`/`disown` combo is generally treated as fine for personal debugging but tech debt the moment it lands in a real script or CI pipeline. Real production systems either register long tasks as proper systemd units / launchd services, or use a language's process-management API to explicitly control every detail — not implicit shell-tool chaining.

### 💸 The High-Stakes Version

In regulated environments, "hand-rolled script + backgrounded Popen + PID polling" is basically an audit red flag — every process needs a clear, traceable lifecycle owner. A `sleep(10)`-and-hope fire-and-forget approach, applied to an irreversible history rewrite, carries roughly the same risk profile as walking away from surgery without closing the incision.

### 🌉 The Cross-Discipline Lens

`start_new_session=True` cutting the child loose is the same logic as clamping a newborn's umbilical cord — the moment it's cut, the infant has to breathe and regulate its own temperature independently. Explicitly redirecting stdout/stderr to a log file is the equivalent of having a ventilator and monitor already hooked up before you cut — detaching cleanly doesn't mean nobody needs to watch the vitals afterward.

### 🥋 Mic-Drop Summary

**`start_new_session=True` only answers "will a terminal signal accidentally kill my child process?" It doesn't answer "did this orphaned process actually finish, and finish correctly?" — that answer only ever comes from the polling and log-checking you write yourself.**

---

## Wrapping Up: What These Four Steps Actually Add Up To

Backup (bundle) → forensics (stash excavation) → surgery (filter-repo rewrite) → making the surgery itself more controllable (Popen daemonization). The common thread underneath all four: **any irreversible operation on Git history should be treated as something that will fail, before you ever run it.**
