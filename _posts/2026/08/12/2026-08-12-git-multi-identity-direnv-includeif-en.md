---
title: "Your Git Identity and Your Push Credential Were Never the Same System"
header:
    image: /assets/images/hd_git.png
date: 2026-08-12
tags:
 - git
 - shell-scripting
 - devops
 - security
 - dotfiles
permalink: /blogs/tech/en/git-multi-identity-direnv-includeif
layout: single
category: tech
---

> The map is not the territory. — Alfred Korzybski

---

# Your Git Identity and Your Push Credential Were Never the Same System

*From "but my gitconfig is correct" to knowing exactly which three places to check*

Kai pinged me with a screenshot of a PR. Every commit had that grey, faceless GitHub avatar next to it — the one that means "this email doesn't belong to any account here." The commits were on a work repo, authored, apparently, by a stranger.

> "I checked. `git config user.email` returns my work address. So what exactly is it lying about?"

I asked them to run it again with one extra flag:

```bash
git config --show-origin --get user.email
```

```
file:/Users/kai/.gitconfig	kai@personal.example.com
```

One line, and the story inverted. The earlier check had been run in a different terminal tab — one whose working directory wasn't inside the repo they thought it was. At the moment the commits were actually made, `includeif` never matched at all.

That's the boring half of the bug. The interesting half is this: **even if `includeif` had matched, and every commit carried the right email, those pushes could still have gone out signed by an entirely different SSH key** — and git would not have said a word about it.

That gap is what this post is about.

**Three things you'll walk away with:**

- A diagnostic one-liner that pins down a multi-identity problem in about ten seconds, and why it probes exactly those three places
- The one-sentence boundary between `includeif` and `direnv` — one swaps your ID card, the other swaps your wallet
- A broken symmetry almost nobody notices: **whose name goes into a commit and whose key gets you through the door are two systems that never compare notes**

The order below isn't the order I actually debugged it in. Real debugging works backwards from the symptom; teaching should work forwards from what you ought to check first.

---

## 1. Why that one-liner probes exactly those three places

For any multi-identity problem, I run this first. It's read-only — it changes nothing:

```bash
echo "--- local  ---"; git -C ~/ws/work/etl-pipeline config --local --get-regexp 'ssh|url|core\.' 2>/dev/null
echo "--- global ---"; git config --global --get-regexp 'ssh|url|includeif|core\.ssh' 2>/dev/null
echo "--- direnv ---"; ls ~/.local/share/direnv/allow 2>/dev/null | head; direnv status 2>&1 | head -8
```

Each section answers a separate question.

### Section 1 — is this repo quietly overriding something?

```bash
git -C ~/ws/work/etl-pipeline config --local --get-regexp 'ssh|url|core\.'
```

- `-C <path>`: run against a specific repo without `cd`-ing there. This matters more than it looks — **the single most common misdiagnosis in multi-identity setups is checking config from the wrong working directory**, which is precisely how Kai got fooled.
- `--local`: reads only that repo's `.git/config`, ignoring global. Highest-precedence layer first.
- `--get-regexp 'ssh|url|core\.'`: regex against key names, pulling out `core.sshCommand` and `url."git@github.com:".insteadOf`-style rewrite rules in one shot.

`url.*.insteadOf` is the one people forget to check. It silently rewrites an `https://` remote into `git@`, sending you down a completely different authentication path than the one you think you're on.

### Section 2 — what do the global rules actually say?

```bash
git config --global --get-regexp 'ssh|url|includeif|core\.ssh'
```

Same idea, aimed at `~/.gitconfig`, with `includeif` added — the mechanism that conditionally pulls in another config file.

Note what this checks: the **rule**, not the **result**. `--get-regexp 'includeif'` tells you what conditions you intended to switch identity on; `--show-origin --get user.email` tells you which one actually won just now. When those two disagree, your bug lives in the match condition.

### Section 3 — has direnv actually been allowed here?

```bash
ls ~/.local/share/direnv/allow 2>/dev/null | head
direnv status 2>&1 | head -8
```

This probes something git cannot see at all: whether you've ever signed off on this directory's `.envrc`. Without that approval, not one environment variable loads — and nothing complains. Git won't error. The AWS CLI won't tell you that you forgot to `direnv allow`. It will just quietly use the default profile and do something you didn't want.

| Section | Question it answers | What you miss by skipping it |
|---|---|---|
| `--local` | Does this repo override the global rules? | You edit `~/.gitconfig` and nothing changes |
| `--global` + `includeif` | What are my identity-switching rules? | The rule exists but its condition never matches |
| `direnv` allow list | Did the env vars load at all? | Git looks fine while AWS / kubectl use the wrong credentials |

> A good diagnostic command earns its keep not from what it prints, but from what it **rules out at the same time**.

---

## 2. includeif: a static ID card

Written in `~/.gitconfig`:

```ini
[includeif "gitdir:~/ws/work/"]
    path = ~/.gitconfig-work

[includeif "gitdir:~/ws/personal/"]
    path = ~/.gitconfig-personal
```

And the file it pulls in:

```ini
# ~/.gitconfig-work
[user]
    name = Kai Chen
    email = kai.chen@work.example.com
[core]
    sshCommand = ssh -i ~/.ssh/work_ed25519
```

Three things to hold onto:

- Triggered by a **directory path match** (`gitdir:`), or by branch name (`onbranch:`, git 2.36+)
- On a match, it merges in `[user]`, `[core]`, and anything else from the target file
- Purely **static and git-internal** — no external process, and `git config --show-origin --get` will tell you exactly which file the winning value came from

🩸 **Hard-earned lesson**: `gitdir:` matches the **repo directory itself** (where `.git` lives), not your shell's current directory. Reach it through a symlink or a git worktree and the match can fail silently. macOS adds a second trap: the filesystem is case-insensitive, but `gitdir:` is case-sensitive by default — `~/ws/Work/` and `~/ws/work/` are the same folder in Finder and two different strings to `includeif`. Use `gitdir/i:` when that bites.

Stop guessing at it. One command settles it:

```bash
git -C <repo> config --show-origin --get user.email
```

The file path in that output is the verdict.

> `includeif` is a rule, not a guarantee. It only exists in the moments the path actually matches.

---

## 3. direnv: a dynamic wallet that needs your signature

An `.envrc` file plus one `direnv allow`:

```bash
# ~/ws/work/etl-pipeline/.envrc
export AWS_PROFILE=work-dev
export GIT_SSH_COMMAND="ssh -i ~/.ssh/work_ed25519"
export KUBECONFIG=~/.kube/work-dev.yaml
```

- Triggered **every time your shell `cd`s into the directory**; the direnv hook sources it, and unloads it when you leave
- Manages **arbitrary environment variables** — not just git, but AWS profiles, Kubernetes contexts, API keys, whatever you need
- **Requires an explicit `direnv allow`** once (exactly what section 3 of the diagnostic was checking), and **editing `.envrc` immediately revokes that approval** until you allow it again

That last point is deliberate design, and it's also the single most common source of "but I changed it and nothing happened."

🩸 **Hard-earned lesson**: `.envrc` is a **real, executing shell script**, not declarative config. Clone an unfamiliar repo that ships its own `.envrc` and you should not reflexively `direnv allow` it — that grants someone else's script arbitrary execution on your machine, automatically, every time you `cd` in. The re-approval prompt isn't friction for its own sake; it turns trust into something you have to perform by hand.

| | includeif | direnv |
|---|---|---|
| Owned by | git internals | the shell (external process + hook) |
| Fires when | any git command runs | you `cd` into or out of the directory |
| Scope | git config keys only | any environment variable |
| Needs approval | no | yes, and edits revoke it |
| Security model | static data, never executed | **executes arbitrary code** |
| How to verify | `git config --show-origin --get` | `direnv status` |

---

## 4. The broken symmetry: whose name, versus whose key

If you read one section, read this one.

Most people carry this model in their head: **"I switched my git identity to work, therefore I'm operating as work."**

That model is wrong. It fuses two things that have nothing to do with each other:

| | Decided by | Verified by anyone? |
|---|---|---|
| Whose name is in the commit | `user.name` / `user.email`, plain text fields | **No.** Put any address you like in there; git records it without comment |
| Whether the push succeeds | which private key the SSH client presents | **Yes.** The server checks the public key and returns `Permission denied` if it's wrong |

`user.email` is **metadata you typed yourself**, and git never validates it. Right now, today, you can run `git -c user.email=linus@kernel.org commit` and produce a commit attributed to Linus. Whether your push lands depends entirely on which private key came out during the SSH handshake — not one byte of which is influenced by `user.email`.

That's the **broken symmetry** at the heart of this setup: two chains that both go by the name "identity," one completely unguarded and one strictly verified, with no consistency check anywhere between them. So you get "the push succeeded" and "the attribution is wrong" at the same time, and you read them as if each confirms the other.

There's a subtler layer underneath:

```ini
# in the file includeif pulls in
[core]
    sshCommand = ssh -i ~/.ssh/work_ed25519
```

```bash
# in .envrc
export GIT_SSH_COMMAND="ssh -i ~/.ssh/personal_ed25519"
```

**The environment variable `GIT_SSH_COMMAND` takes precedence over the `core.sshCommand` config key.** So the work key you carefully wired up through `includeif` gets silently overruled by a variable left sitting in your shell — and `git config --get core.sshCommand` will keep reporting the work key, because it's reporting configuration, not behavior.

To see what's actually happening, you have to go around git's own account of itself:

```bash
# who is really driving SSH
echo "$GIT_SSH_COMMAND"
git config --show-origin --get core.sshCommand

# who the server thinks you are (GitHub answers with the account name)
ssh -T git@github.com
```

That last command is the most honest one in the whole toolkit. It doesn't ask your config. It asks the other side.

---

## 5. The two systems as one chain

Here's the full path, with each system owning one link:

```
cd into ~/ws/work/etl-pipeline/
   ↓ direnv loads .envrc (only if allowed)
AWS_PROFILE=work-dev + GIT_SSH_COMMAND points at the work key
   ↓ a git command runs, includeif matches gitdir
user.email becomes the work address, written into the commit
   ↓ push, SSH handshake
the server authenticates the key — the key, never the email
```

Break any link and you get a different symptom, none of which names the broken link:

| Symptom | Broken link | Check first |
|---|---|---|
| Commits attributed to your personal email, but the push worked | `includeif` didn't match; the key was fine | `git config --show-origin --get user.email` |
| `Permission denied (publickey)` | Identity right, key never arrived | `echo $GIT_SSH_COMMAND`; `ssh -T git@github.com` |
| Git behaves perfectly, AWS / kubectl use the wrong account | direnv was never allowed | `direnv status` |
| Edited `.envrc`, still getting the old values | the edit revoked the approval | `direnv allow` |
| Config clearly says work key, personal key is being used | env var overrode the config key | `echo $GIT_SSH_COMMAND` |

Look at those last two rows. Both are cases where you believe you already fixed it. They're the expensive ones, because they raise no error at all — they just quietly do the wrong thing.

---

## Do this today

1. **Run `git -C . config --show-origin --get user.email` in your work repo right now.** Not `--get` — `--show-origin --get`. Look at which file that value came from. If it's `~/.gitconfig` rather than the work config you expected, your `includeif` has never once fired.
2. **Run `ssh -T git@github.com`** and see what the server calls you. It's the only answer that doesn't depend on your local config telling the truth.
3. **`echo "$GIT_SSH_COMMAND"`.** If it's non-empty and you don't remember setting it, it is currently overriding every `core.sshCommand` you have.
4. **Rewrite one `gitdir:` pattern as an absolute path and re-test**, to rule out a symlink or worktree quietly breaking the match.
5. **Put those three checks into a `git-whoami` function in your dotfiles.** This is the highest-value item on the list. Everything above is currently tribal knowledge living only in your head, and in three months you will re-derive all of it from scratch. Turn it into an artifact that executes and you never reason about it again:

   ```bash
   git-whoami() {
     echo "email : $(git config --show-origin --get user.email 2>/dev/null || echo '(none)')"
     echo "ssh   : ${GIT_SSH_COMMAND:-$(git config --get core.sshCommand || echo '(default)')}"
     echo "aws   : ${AWS_PROFILE:-'(default)'}"
     direnv status 2>/dev/null | grep -i 'loaded rc\|allowed' || echo "direnv: n/a"
   }
   ```

6. **`cat .envrc` before you `direnv allow` any repo you didn't write.** That's not fastidiousness, it's a security boundary.

---

*Your config files record what you meant. Your runtime environment records what you did. Every multi-identity incident happens in the gap where those two drift apart and nothing raises a hand.*
