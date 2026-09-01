---
title: "Debugging Multi-Identity Git Setups: What a Diagnostic One-Liner Teaches About includeif and direnv"
date: 2026-08-12
categories: [engineering, git, shell]
tags: [git, direnv, includeif, ssh, dotfiles]
---

Switching between a corporate repo (Macquarie SSO) and personal repos, the thing you dread most is pushing with the wrong identity, or having your AWS profile silently mismatch. This post walks through a real debugging session: starting from one diagnostic command and ending with a clear mental model of `includeif` vs `direnv` — two mechanisms that get mixed up constantly.

## Part 1: Breaking Down a Diagnostic Command

The starting point was this command (explained only, not executed):

```bash
echo "--- local ---"; git -C ~/ws/qa/edr-nonstandard-etl config --local --get-regexp 'ssh|url|core\.' 2>/dev/null
echo "--- global ---"; git config --global --get-regexp 'ssh|url|includeif|core\.ssh' 2>/dev/null
echo "--- direnv allow list ---"; ls ~/.local/share/direnv/allow 2>/dev/null | head; direnv status 2>&1 | head -8
```

### Section 1 — Local repo git config

```bash
git -C ~/ws/qa/edr-nonstandard-etl config --local --get-regexp 'ssh|url|core\.'
```

- `-C <path>`: run a git command against a specific repo without `cd`-ing there
- `config --local`: reads only that repo's own `.git/config`, ignoring global settings
- `--get-regexp 'ssh|url|core\.'`: regex-matches key names to surface anything related to `ssh`, `url`, or `core.` (e.g. `core.sshCommand`, `url."xxx".insteadOf` rewrite/proxy rules)

### Section 2 — Global git config

```bash
git config --global --get-regexp 'ssh|url|includeif|core\.ssh'
```

Same idea, but against `~/.gitconfig`, with `includeif` added — the mechanism for conditionally pulling in a different config file, commonly used for "this SSH key for work directories, that one for personal."

### Section 3 — direnv authorization list

```bash
ls ~/.local/share/direnv/allow 2>/dev/null | head
direnv status 2>&1 | head -8
```

Taken together, this command answers one question: "which SSH identity / URL rewrite rules does this repo actually use, and has direnv been allowed to run here?" — a classic checklist for multi-identity dev environments.

## Part 2: includeif vs direnv, in One Line

> **`includeif` decides *who you are* (git identity). `direnv` decides *what environment you're in* (env vars / PATH / secrets). One swaps your ID card, the other swaps your wallet.**

### includeif: auto-switching git identity by directory

Defined in `~/.gitconfig`:

```ini
[includeif "gitdir:~/ws/mq/"]
    path = ~/.gitconfig-macquarie

[includeif "gitdir:~/ws/personal/"]
    path = ~/.gitconfig-personal
```

- Triggered by a **directory path match** (`gitdir:`), or by branch name (`onbranch:`, git 2.36+)
- Once matched, it merges in `[user] name/email`, `[core] sshCommand`, etc. from the target file
- Purely **static, git-internal** — no external process involved, and `git config --get` shows the merged result directly

🩸 **Hard-earned lesson**: `gitdir:` matches the **repo directory itself** (where `.git` lives). If you got there via a symlink or a git worktree, the path match can silently fail — use `gitdir/i:` (case-insensitive) or debug with the absolute path.

### direnv: auto-loading shell environment by directory

`.envrc` file + `direnv allow`:

```bash
# ~/ws/mq/edr-nonstandard-etl/.envrc
export AWS_PROFILE=mqu-dev
export GIT_SSH_COMMAND="ssh -i ~/.ssh/mq_id_ed25519"
```

- Triggered every time the shell `cd`s into the directory; the direnv hook auto-sources the file
- Manages **arbitrary environment variables** — not just git, but AWS profiles, Kubernetes contexts, API keys, anything
- **Requires explicit `direnv allow`** once (this is exactly what the original command's allow-list check was verifying) — and editing `.envrc` invalidates that trust, requiring re-allow, to stop a malicious repo from silently running code

🩸 **Hard-earned lesson**: code inside `.envrc` is a **real, executable shell script**, not declarative config. If you `git pull` an unfamiliar repo that ships its own `.envrc`, don't blindly `direnv allow` it — that's equivalent to letting someone else's script run arbitrary commands on your machine.

### Putting it together

`includeif` only changes your git-level identity — it does **not** automatically load the matching SSH key into your agent, nor switch your AWS profile. So the full chain looks like:

```
cd into ~/ws/mq/edr-nonstandard-etl/
   ↓ direnv auto-loads
GIT_SSH_COMMAND points to the mq key + AWS_PROFILE=mqu-dev
   ↓ includeif matches gitdir
git identity switches to the macquarie email
```

Each system owns one link in the chain — **if either link is misconfigured, you get "pushed with the wrong identity" or "AWS permissions don't match" bugs**, and debugging only one side will miss the other.

## Takeaway

- `includeif` = static, git-internal, owns identity
- `direnv` = dynamic, shell-level, owns environment variables, and requires explicit trust
- A proper multi-identity dev setup needs both working together — checking only one in isolation can hide the real problem

