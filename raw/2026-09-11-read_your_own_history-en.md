title
Reading Your Own History: git log, git diff and Revision Ranges (EN)
content
# Reading Your Own History: A Field Guide to `git log`, `git diff` and Revision Ranges

> *"Your branch is ahead of 'origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade' by 18 commits."*

Every engineer has hit this line. Eighteen commits of your own work, sitting on your laptop, about to be pushed into a review that someone else has to read. Before you push, you want to know: **what exactly is in there?**

This post walks from that one line of `git status` output down into the machinery underneath — revision ranges, diff formats, and the handful of plumbing commands that turn "18 commits" into a story you can actually explain in a pull request description.

---

## 1. What "ahead by 18 commits" actually means

`git status` is not talking to the server. It is comparing two local refs:

```
refs/heads/DATAPLATCORE-1265-airflow-2.11.2-upgrade ← your branch
refs/remotes/origin/DATAPLATCORE-1265-... ← your cached snapshot of the remote
```

That second ref is a **remote-tracking branch**: a local file recording where the remote *was* the last time you talked to it. Git then walks the commit graph and counts commits reachable from one but not the other.

> ⚠️ **The gotcha:** "ahead by 18, nothing to commit" does **not** mean the remote is unchanged. If a teammate pushed an hour ago and you haven't fetched, Git has no idea. Run `git fetch` first — it updates the remote-tracking ref without touching your working tree. Only then is the ahead/behind count trustworthy.

```bash
git fetch # refresh the cached remote refs
git status -sb # short branch line: ## branch...origin/branch [ahead 18]
```

> 🎉 **Fun fact:** `git fetch` is one of the few network commands that is essentially always safe. It writes only to `refs/remotes/*` and the object database. Nothing in your working tree, index, or local branches moves. `git pull` is the dangerous one, because it is `fetch` + `merge` (or `rebase`) glued together.

---

## 2. `@{u}` — stop typing that branch name

A branch name like `DATAPLATCORE-1265-airflow-2.11.2-upgrade` is a lot of keystrokes. Git has shorthand:

| Shorthand | Means |
|---|---|
| `@{u}` or `@{upstream}` | The upstream branch this one tracks |
| `@{push}` | Where a `git push` would go (differs under triangular workflows) |
| `@` | Bare shorthand for `HEAD` |
| `HEAD~3` | Three commits back along first parents |
| `HEAD^2` | The **second parent** of a merge commit |
| `HEAD@{2}` | Where `HEAD` pointed two moves ago (reflog, not graph!) |

`@{u}` resolves via your config:

```bash
git config --get branch.DATAPLATCORE-1265-airflow-2.11.2-upgrade.remote # origin
git config --get branch.DATAPLATCORE-1265-airflow-2.11.2-upgrade.merge # refs/heads/...
```

If those are missing, `@{u}` errors out with *"no upstream configured"* and you must spell the ref out in full.

> 🎉 **Fun fact:** `~` and `^` are easy to mix up. `^` means "pick a parent" (`HEAD^2` = second parent). `~` means "walk back, always taking the first parent" (`HEAD~2` = grandparent). So `HEAD~2 == HEAD^^`, but `HEAD^2 != HEAD~2`. On Windows `cmd.exe`, `^` is an escape character, which is why you'll see `HEAD^^^` mysteriously fail there.

> 🎉 **Fun fact:** the `@{...}` reflog syntax has a date form. `git log master@{yesterday}` or `HEAD@{2.days.ago}` asks "where was this ref then?" — which is how you recover from a bad rebase you did on Tuesday.

---

## 3. Revision ranges are set arithmetic, not intervals

This is the single most useful mental model in Git. `A..B` is **not** "the commits between A and B" in a linear sense. It is shorthand for:

```
^A B → { commits reachable from B } minus { commits reachable from A }
```

The `^` prefix means "exclude everything reachable from here". So these are identical:

```bash
git log @{u}..HEAD
git log HEAD ^@{u}
git log ^@{u} HEAD
```

And you can compose freely — three-way exclusions, multiple tips:

```bash
git log HEAD ^main ^release/2.10 # on my branch, not in main, not in the release
git log v2.11.2 v2.11.1 ^v2.10.0 # union of two tags minus an older one
```

> 🎉 **Fun fact:** because it's set arithmetic on a DAG, `A..B` can return commits that are *chronologically older* than A. Reachability has nothing to do with timestamps. This is why "the commits between two releases" is a subtler question than it looks.

### The `...` trap

Three dots means **different things** in `git log` and `git diff`. This trips up experienced people:

| Command | Meaning |
|---|---|
| `git log A...B` | **Symmetric difference** — commits in either, but not both |
| `git diff A...B` | Diff from the **merge base** of A and B, to B |
| `git diff A..B` | Plain diff of the two endpoints (identical to `git diff A B`) |

So in `log`, `...` is *wider* than `..`. In `diff`, `...` is *narrower* — it ignores everything that happened on A since they diverged. For code review, `git diff main...HEAD` is almost always what you want: "what did **I** change", not "how do the two tips differ".

Since Git 2.30 there's an explicit spelling, which is worth preferring because it can't be misread:

```bash
git diff --merge-base main HEAD
```

> 🎉 **Fun fact:** GitHub's "Files changed" tab on a PR shows a three-dot diff (merge-base based). That's why a PR can look clean even when the target branch has moved on wildly — and why "it's green on GitHub" doesn't guarantee it merges cleanly.

---

## 4. Five levels of zoom

Same range, escalating detail. Pick the smallest one that answers your question.

### Level 1 — the list

```bash
git log --oneline @{u}..HEAD
git log --oneline --graph @{u}..HEAD # add topology if merges exist
git rev-list --count @{u}..HEAD # → 18
```

> 🎉 **Fun fact:** `--graph` silently turns on `--topo-order`, so parents never appear before children. Without it, `git log` sorts by **committer date**, which can look scrambled on a rebased branch.

### Level 2 — which files, per commit

```bash
git log --stat @{u}..HEAD # histogram per commit
git log --name-status --oneline @{u}..HEAD # status letters, compact
git log --numstat --oneline @{u}..HEAD # machine-parsable: added deleted path
```

Status letters: `A` added, `M` modified, `D` deleted, `R` renamed, `C` copied, `T` type change (e.g. file → symlink).

> 🎉 **Fun fact:** the `+++---` bars in `--stat` are **scaled to your terminal width**, not literal counts. A file showing `5 +++--` might be 3 insertions and 2 deletions — or 300 and 200. Never parse `--stat`; use `--numstat`, which is raw numbers and tab-separated.

### Level 3 — the full patches

```bash
git log -p @{u}..HEAD
git log -p --reverse @{u}..HEAD # oldest first — reads like a narrative
git log -p @{u}..HEAD -- requirements.txt # scope to one path
```

`--reverse` is underrated. Reviewing 18 commits in the order they were written is far easier than backwards.

### Level 4 — the aggregate (all 18 as one change)

This is what your reviewer effectively sees:

```bash
git diff --stat @{u}..HEAD # summary
git diff --name-status @{u}..HEAD # unique files touched
git diff --shortstat @{u}..HEAD # one line: N files changed, X insertions(+), Y deletions(-)
git diff @{u}..HEAD # the whole thing
```

The difference matters. If you added a file in commit 3 and deleted it in commit 14, `git log --stat` shows both events; `git diff` shows nothing. Churn versus net effect.

### Level 5 — one commit, up close

```bash
git show <sha> # message + full diff
git show --stat <sha> # message + file list
git show <sha> -- path/to/file # just one file's changes
git show <sha>:path/to/file # the file's *contents* at that commit (no diff)
```

> ⚠️ **The merge-commit gotcha:** `git show <merge-sha>` often prints a header and *no diff at all*. By default Git shows a **combined diff** (`--cc`), which only displays hunks that differ from **every** parent — i.e. only conflict resolutions. A clean merge legitimately has nothing to show. Use `git show -m <sha>` for one diff per parent, or `git show --first-parent <sha>` for "what did this merge bring into my branch".

> 🎉 **Fun fact:** note the two colon syntaxes. `git show A -- file` means "the diff of *file* in commit A". `git show A:file` means "the *blob* at path file in commit A". One character, completely different output. The second is how you cat an old version without checking anything out.

---

## 5. Power tools worth knowing

### The pickaxe: when did this line appear?

```bash
git log -S 'apache-airflow==' --oneline # commits changing the count of that string
git log -S 'OLLAMA_HOST' --oneline -- . # when was this env var introduced/removed?
git log -G 'ollama_(url|host)' --oneline # regex match anywhere in the diff text
```

`-S` counts occurrences and reports commits where the number changed. `-G` matches the diff text with a regex. `-S` is more precise for "added or removed"; `-G` catches "moved or reformatted".

> 🎉 **Fun fact:** the name is literal — the Git docs call `-S` "the pickaxe", because you're digging through strata of history looking for one seam. It has been in Git since the very early days and remains the fastest way to answer "who introduced this?" when `git blame` only shows the last person to reindent it.

### Trace one function through time

```bash
git log -L :parse_dag:dags/loader.py # follow a function by name
git log -L 250,270:blogs_client.py # follow a line range
```

Git will find the function boundaries itself (using the same heuristics as diff hunk headers) and show you every patch that touched it.

### Did my rebase change anything? `range-diff`

Essential on a long-lived upgrade branch that you keep rebasing onto `main`:

```bash
git range-diff @{u}...HEAD # compare the two versions of the series
git range-diff main old-tip new-tip # explicit form
```

It's a **diff of diffs**: it pairs up commits from two versions of a series and shows how each patch changed. If your rebase should have been mechanical, `range-diff` proves it.

> 🎉 **Fun fact:** `range-diff` (Git 2.19, 2018) came out of the Git mailing-list workflow, where maintainers review patch series v1 → v2 → v3 by email. It uses the same commit-pairing engine as `git cherry` — a **patch-id**, which is a hash of the diff with whitespace and line numbers normalised. That's why a cherry-picked commit is recognisable even though its SHA is completely different.

```bash
git log --cherry-mark --oneline @{u}...HEAD # = already upstream, + only here
git cherry -v @{u} # - equivalent patch exists, + it doesn't
```

### Rename detection is a lie (a useful one)

Git stores **snapshots**, not operations. There is no "rename" recorded anywhere. When you see `R096 old/path.py → new/path.py`, Git computed that at display time by comparing content similarity — default threshold 50%.

```bash
git log --stat -M @{u}..HEAD # rename detection (on by default in modern Git)
git log --stat -M20% @{u}..HEAD # be more aggressive
git log --stat -C @{u}..HEAD # also detect copies
git log --follow -- path/to/file.py # follow a single file across renames
```

`R100` means a pure rename with identical content. `--follow` only works with exactly one path — it's a bolted-on hack, not a first-class feature.

> 🎉 **Fun fact:** this design decision is why Git handles "I moved a function from one file to another" so gracefully compared with systems that track renames explicitly. It's also why `git log --follow` gets confused when you rename and heavily edit in the same commit — there's simply no metadata to fall back on.

### Formatting and the two dates

```bash
git log --pretty=format:'%h %ad %an %s' --date=short @{u}..HEAD
git log --pretty=fuller @{u}..HEAD # shows AuthorDate *and* CommitDate
git shortlog -sn @{u}..HEAD # commits grouped and counted by author
```

Common placeholders: `%H` full hash, `%h` abbreviated, `%an`/`%ae` author name/email, `%ad` author date, `%cd` committer date, `%s` subject, `%b` body, `%d` ref decorations, `%C(auto)` colour.

> 🎉 **Fun fact:** every commit carries **two** identities and **two** timestamps — author and committer. `git rebase` and `git cherry-pick` preserve the author date but reset the committer date. That's why a freshly rebased branch shows commits "from three weeks ago" that were technically created five minutes ago, and why `git log` (sorting by committer date) and `git log --date-order` can disagree about ordering.

> 🎉 **Fun fact:** the abbreviated SHA in `--oneline` isn't a fixed 7 characters. Since Git 2.11, `core.abbrev` defaults to `auto`, sizing the prefix from the number of objects in your repo to keep collisions unlikely. The Linux kernel now needs 12. Seven was only ever a good default for a small repo.

---

## 6. Applied: auditing an Airflow upgrade branch

Concretely, for `DATAPLATCORE-1265-airflow-2.11.2-upgrade`, the useful sequence is:

```bash
# 0. make the count honest
git fetch

# 1. net footprint — is this confined to pins, or has it leaked into DAGs?
git diff --stat @{u}..HEAD

# 2. the exact set of files a reviewer will open
git diff --name-status @{u}..HEAD

# 3. narrative order, for writing the PR description
git log --oneline --reverse @{u}..HEAD

# 4. the risky bits, in full
git diff @{u}..HEAD -- requirements.txt constraints.txt Dockerfile

# 5. when did that provider pin actually move?
git log -S 'apache-airflow-providers-google' -p @{u}..HEAD

# 6. did anything sneak into the DAGs directory?
git log --oneline @{u}..HEAD -- dags/

# 7. after the next rebase onto main, prove nothing changed
git range-diff @{u}...HEAD
```

Step 1 is the highest-value single command. On an upgrade branch, a `--stat` that touches only constraint and Dockerfile lines is a very different review from one that also rewrites twelve DAGs.

---

## 7. Browsing interactively

When you'd rather click than type:

```bash
gitk @{u}..HEAD # the original GUI, ships with Git
tig @{u}..HEAD # terminal UI, vim-ish keys
git log --oneline | fzf --preview 'git show --color=always {1}' # poor man's tig
```

> 🎉 **Fun fact:** `gitk` was written by **Paul Mackerras** — the same person who wrote the Linux PPP daemon and maintained the PowerPC kernel port — in Tcl/Tk, within weeks of Git's first release in April 2005. It still ships in the official Git distribution twenty years later, and it still looks exactly like Tcl/Tk. `tig`, meanwhile, is just "git" spelled backwards.

---

## 8. Cheat sheet

| Question | Command |
|---|---|
| How many unpushed commits? | `git rev-list --count @{u}..HEAD` |
| What are they? | `git log --oneline @{u}..HEAD` |
| Which files, per commit? | `git log --name-status --oneline @{u}..HEAD` |
| Which files, in total? | `git diff --name-status @{u}..HEAD` |
| How big is this change? | `git diff --shortstat @{u}..HEAD` |
| Full combined diff (reviewer's view) | `git diff @{u}..HEAD` |
| Read it as a story | `git log -p --reverse @{u}..HEAD` |
| One commit in detail | `git show <sha>` |
| A merge commit's real diff | `git show -m <sha>` |
| File contents at an old commit | `git show <sha>:path` |
| Who introduced this string? | `git log -S 'string' --oneline` |
| History of one function | `git log -L :func:file` |
| Did my rebase alter the patches? | `git range-diff @{u}...HEAD` |
| Both sides after the remote moved | `git log --oneline --left-right @{u}...HEAD` |

---

## 9. Three last pieces of trivia

- **`git rev-list` is the engine.** `git log` is a porcelain wrapper around the same graph traversal, with diff machinery attached. Anything `log` can select, `rev-list` can select — which is why `rev-list` shows up constantly in scripts and in Git's own test suite.
- **The empty tree has a famous hash:** `4b825dc642cb6eb9a060e54bf8d69288fbee4904`. Diff against it to see an entire commit as pure additions, which is the standard trick for showing "the diff" of a root commit that has no parent. (Or just use `git show --root <sha>`.)
- **SHA-1 is not what you think it is.** After the SHAttered collision in 2017, Git 2.13 shipped a hardened SHA-1 implementation that detects collision attempts and refuses to hash them. Git also grew a full SHA-256 object-format mode, though interoperability means almost every repository you'll ever touch is still SHA-1.

---

*Written for engineers who inherited a branch, a ticket number, and a vague sense of dread. `git fetch`, then `git diff --stat @{u}..HEAD`. Start there.*