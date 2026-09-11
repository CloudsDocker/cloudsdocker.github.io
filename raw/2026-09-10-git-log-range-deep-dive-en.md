title
git-log-range-deep-dive.en.md
content
---
title: "One git log Command, Explained Properly"
subtitle: "What master..origin/branch is actually asking"
date: 2026-09-10
tags: [git, version-control, engineering-practice, code-review]
lang: en
---

# One `git log` Command, Explained Properly

You're reviewing an Airflow upgrade branch and a colleague types this:

```bash
git log master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade --oneline
```

You can read it. Can you *explain* it? This post starts from that single command and works outward until Git's **revision range** syntax is fully demystified — including `..` vs `...`, `^` vs `--not`, and the trap that catches almost everyone: **`...` means different things in `git log` and `git diff`.**

---

## The one-line answer

The command asks:

> **"Which commits exist on the remote branch `origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade` that my local `master` does not have?"**

One line per commit.

---

## 1. Breaking it down

| Fragment | Meaning |
|---|---|
| `git log` | Walks the commit graph by **reachability** and prints a commit list |
| `master` | The commit your local `master` branch points at (a commit-ish) |
| `..` | The two-dot range operator |
| `origin/...upgrade` | A **remote-tracking branch** — a *snapshot* of remote state as of your last `git fetch` |
| `--oneline` | Shorthand for `--pretty=oneline --abbrev-commit`: abbreviated SHA + subject, one per line |

The branch name `DATAPLATCORE-1265-airflow-2.11.2-upgrade` carries no syntactic meaning — it's a team convention: **Jira ticket ID + description** (upgrade Airflow to 2.11.2). Good branch names make `git log --oneline` output self-documenting, which is its own form of engineering hygiene.

---

## 2. What `..` actually means

```
A..B ≡ B ^A ≡ B --not A
```

As a set expression: **commits reachable from B, minus commits reachable from A.**

Visually:

```
D---E---F origin/DATAPLAT...-upgrade
/
A---B---C master
```

- `master..origin/...` → prints `F E D` (new work on the upgrade branch)
- `origin/.....master` → prints `C` (on master, not yet merged into the branch)

**Reversing the order gives a completely different answer.** This is the single most common misuse.

Three things to internalise:

1. **This is a set difference over commits, not a diff.** For file content you need `git diff` — and you need three dots (§4).
2. **Output is reverse-chronological by default**, not topological. Add `--topo-order` if you need graph order.
3. **Empty output means fully merged** — and an empty result is itself useful signal.

---

## 3. One level deeper: `^` and `--not` are the real primitives

`..` is sugar. What `git log` really does is **traverse the graph from a set of starting points**:

- A bare ref = an **include** (positive starting point)
- A ref prefixed with `^` = an **exclude**: "don't show me anything reachable from this"

So `B ^A` reads: *start at B, walk backwards, prune everything A can also reach.*

Verify it yourself:

```bash
git log --oneline master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
git log --oneline origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade ^master
# Identical output
```

**Why bother knowing the primitive?** Because `^` composes arbitrarily and `..` doesn't:

```bash
# Commits on feature that are on neither master nor develop
git log --oneline feature ^master ^develop

# Commits on B or C but not on A
git log --oneline B C ^A
```

`..` expresses *one minus one*. `^` expresses *many minus many*. That gap is the line between using Git and understanding it.

> **Shell note:** `^` needs quoting or escaping in some shells (certain zsh setups, Windows CMD). Write `'^master'`, or just use `--not master`.

---

## 4. The two faces of `...` (the big trap)

**The same `...` token means different things in `git log` and `git diff`.** This is a widely acknowledged piece of historical baggage in Git's UI.

### 4.1 `git log a...b` = symmetric difference

Set expression: `(a ∪ b) - (a ∩ b)` — **everything unique to either side.**

Equivalent primitive form:

```
a...b ≡ a b --not $(git merge-base --all a b)
```

```
D---E---F b
/
A---B---C a

git log a...b → C F E D (unique to both sides)
git log a..b → F E D (unique to b only)
```

It only becomes genuinely useful with `--left-right`:

```bash
git log --oneline --left-right --graph \
master...origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
# < abc1234 only on master
# > def5678 only on the branch
```

### 4.2 `git diff a...b` = "b relative to the merge base"

Equivalent to:

```bash
git diff $(git merge-base a b) b
```

In other words: **ignore everything that happened on `a` since the fork point**, and show only what `b`'s line of development did.

Contrast with `git diff a..b` (which is just `git diff a b`): a **direct comparison of two endpoint snapshots**. That renders "things added on `a`" as *deletions* in `b` — almost never what you want.

### 4.3 The rule to memorise

```bash
# "Which commits does this PR introduce?" — log, two dots
git log --oneline master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade

# "Which code does this PR change?" — diff, three dots
git diff master...origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade

# Files touched + line counts
git diff --stat master...origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
```

**Mnemonic: two dots for `log`, three dots for `diff`.**

GitHub and GitLab PR views render exactly the three-dot `diff` semantics — which is why other people's changes on `master` don't pollute your PR.

---

## 5. What empty output tells you

Strictly: **the set of commits reachable from B is a subset of those reachable from A.** In Git terms, **B is an ancestor of A** — B has been fully merged into A.

Real-world cases:

| Case | Notes |
|---|---|
| B already merged into A | Most common: the PR has landed |
| A and B point at the same commit | Freshly fetched, fully in sync |
| B is older than A | Branch created but never committed to |

**Don't script on "is the log output empty".** Use precise tools:

```bash
# Exit 0 = is an ancestor (i.e. merged), 1 = not
git merge-base --is-ancestor \
origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade master
echo $?

# Or count
test "$(git rev-list --count master..origin/DATAPLAT...upgrade)" -eq 0
```

> ⚠️ **Critical caveat:** empty output does **not** mean the two sides have identical content. If a branch landed via **squash merge** or **rebase**, every SHA changed — so `master..branch` may be **non-empty** while the code is byte-for-byte the same.
>
> **"Set of commits" and "file content" are orthogonal dimensions.** Next section unpacks that.

---

## 6. Why a commit you *know* is on master still shows up

**Root cause:** a commit's identity is its hash (SHA-1/SHA-256), and that hash covers the **parent pointers, tree, author, committer, timestamps and message**. Change any one of them and the SHA changes — **even if the diff is identical.**

So "the same change" can be two entirely unrelated commit objects as far as Git is concerned. Operations that produce these twins:

| Operation | What happens |
|---|---|
| `cherry-pick` | New parent → new SHA |
| `rebase` | Whole line replayed → all new SHAs |
| Squash merge | N commits collapsed into one brand-new commit |
| `git am` / patch-over-email | Commit rebuilt from a diff |
| `--amend` / message edit | Content unchanged, SHA changed |

### 6.1 The remedy: `--cherry-mark` / `--cherry-pick` / `--cherry`

Git identifies **equivalent commits** using **patch-id**: a normalised hash of the diff itself, insensitive to line-number offsets and context.

```bash
# Mark equivalents: '=' present on both sides, '+' genuinely unique
git log --oneline --left-right --cherry-mark master...origin/DATAPLAT...upgrade

# Filter equivalents out entirely
git log --oneline --left-right --cherry-pick master...origin/DATAPLAT...upgrade

# --cherry is a shorthand ≈ --right-only --cherry-mark --no-merges
git log --oneline --cherry master...origin/DATAPLAT...upgrade
```

Note: these options **only make sense with three-dot symmetric difference** — pairing requires walking both sides. They're inert with `..`.

### 6.2 Where patch-id breaks down (know the edges)

- **Merge commits have no patch-id** → pair with `--no-merges`
- If the cherry-pick **involved conflict resolution**, content differs, patch-id won't match, and it still shows as unique
- Empty commits (no diff) can't be paired

### 6.3 An alternative investigation path

```bash
# Search all refs by message keyword
git log --oneline --all --grep='DATAPLATCORE-1265'

# Which branches contain this commit?
git branch -a --contains <sha>

# Trace cherry-pick provenance (only if -x was used originally)
git log --oneline --grep='cherry picked from'
```

**Practice worth adopting:** mandate `cherry-pick -x` team-wide. It records `(cherry picked from commit <sha>)` in the message and cuts future archaeology cost by an order of magnitude.

---

## 7. Three pitfalls you must remember

### 1. `origin/xxx` is a cache, not the live remote

Remote-tracking branches only move when you `git fetch` or `git pull`. Without a fetch, you're reasoning about a world several days old:

```bash
git fetch -p origin # -p / --prune also cleans up deleted remote branches
```

`-p` matters: when a remote branch is deleted, your local `origin/xxx` doesn't vanish on its own, and you may be comparing against a branch that no longer exists.

### 2. `master` means your **local** master

A stale local master will list a pile of commits that are *already on the remote master*. If you mean the remote, say so:

```bash
git log --oneline origin/master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
```

**Rule of thumb: when assessing branch progress, put `origin/` on *both* sides** so local state can't distort the answer.

### 3. Name ambiguity and the `--` separator

Dots in a branch name (`2.11.2`) are usually fine, but if a tag and a branch share a name, Git's resolution precedence will confuse you. Disambiguate:

```bash
# Fully qualified refs
git log --oneline refs/heads/master..refs/remotes/origin/DATAPLAT...upgrade

# Use -- to declare "what follows is a path, not a ref"
git log --oneline master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade --
```

---

## 8. Advanced variants: expanding the toolkit

```bash
# Just the count
git rev-list --count master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade

# Behind/ahead in one shot (left = behind, right = ahead)
git rev-list --left-right --count master...origin/DATAPLAT...upgrade

# Graph + ref decoration
git log master..origin/...upgrade --oneline --graph --decorate

# Custom format: short SHA + date + author + subject
git log master..origin/...upgrade --pretty='%h %ad %an %s' --date=short

# Show which files each commit touched
git log master..origin/...upgrade --oneline --name-status

# Only commits that touched Airflow dependencies (path filter)
git log master..origin/...upgrade --oneline -- requirements.txt Dockerfile constraints.txt

# Skip merges to see the "real" work
git log master..origin/...upgrade --oneline --no-merges

# Compare against the current branch's upstream (@{u} = @{upstream})
git log @{u}..HEAD --oneline # ahead of upstream (unpushed)
git log HEAD..@{u} --oneline # behind upstream (unpulled)
```

### Aliases worth putting in `~/.gitconfig`

```ini
[alias]
# Unpushed / unpulled
ahead = log --oneline @{u}..HEAD
behind = log --oneline HEAD..@{u}
# Ahead/behind counts
ab = !git rev-list --left-right --count @{u}...HEAD
# What commits does this branch introduce relative to a base?
new = "!f() { git log --oneline --no-merges ${2:-origin/master}..$1; }; f"
# What code does this branch change? (PR view)
pr = "!f() { git diff --stat ${2:-origin/master}...$1; }; f"
# Filter out cherry-picked duplicates
real = "!f() { git log --oneline --left-right --cherry-pick --no-merges ${2:-origin/master}...$1; }; f"
```

---

## 9. When you'd reach for this

1. **Before a code review** — see the commit skeleton of the upgrade branch before reading any code.
2. **Writing a PR description or release notes** — `git log --oneline --no-merges base..head` is a ready-made draft.
3. **Deciding whether to rebase** — run it in reverse (`origin/...upgrade..origin/master`); non-empty means the branch is behind the mainline.
4. **CI debugging** — confirm a specific fix is really on the branch (add `--cherry-pick` so a rebase doesn't fool you).
5. **Pre-release sanity check** — `git rev-list --left-right --count origin/master...origin/release` shows both gaps at a glance.

---

## 10. Self-test: answer these and you've got it

| # | Question | Answer |
|---|---|---|
| 1 | The primitive form of `A..B`? | `B ^A` / `B --not A`. `^` composes with many refs; `..` can't |
| 2 | What does empty output mean? | Everything reachable from B is contained in A — B is an ancestor of A. But **not** that content is identical (squash/rebase) |
| 3 | Are `git log a...b` and `git diff a...b` the same? | **No.** log = symmetric difference; diff = b relative to merge base. Two dots for log, three for diff |
| 4 | Why does a commit already on master appear? | cherry-pick / rebase / squash minted new SHAs. Filter with `--cherry-pick` (patch-id based) |
| 5 | Can abbreviated SHAs from `--oneline` collide? | In principle yes; Git auto-lengthens based on object count, and `core.abbrev` lets you pin it |

---

## Wrapping up

- `..` is set difference; `...` (in `log`) is symmetric difference; both compile down to `^` / `--not` graph traversal
- **Two dots for `log`, three for `diff`** — one sentence that avoids the biggest trap
- Commit identity is a hash: **identical content ≠ identical commit**. `--cherry-pick` is the patch-id-level cure
- Always `git fetch -p origin` first, or your elegant conclusion rests on a stale cache

Treat Git as a directed acyclic graph and these commands as a query language over it, and a lot of confusion dissolves at once.

---

## Appendix: while we're here — deleting to end of file in your editor

Back to the editor after the Git archaeology. In LazyVim (and any Vim/Neovim), place the cursor on the starting line and, in Normal mode, press:

```
dG
```

`d` is the delete operator, `G` jumps to the last line — together, **delete from the current line through end of file** (linewise).

Useful variants:

| Command | Effect |
|---|---|
| `dG` | Current line → end of file |
| `:.,$d` | Ex-command equivalent |
| `VG` then `d` | See the selection highlighted first |
| `dgg` | Current line → start of file |
| `d}` | Delete to end of current paragraph/block |
| `D` or `d$` | Delete to end of **line** only, keeping the line |
| `"_dG` | Delete without clobbering the unnamed register (black-hole register) |

`u` undoes it if the range wasn't what you expected. Worth noticing: `d` + motion and Git's range syntax share a design idea — **operator plus range, composed orthogonally.** Learn one axis and the combinations come free.