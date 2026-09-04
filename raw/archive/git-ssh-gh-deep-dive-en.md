---
title: "One ssh Command, Nine Deep-Water Traps in Git / SSH / gh"
date: 2026-09-03
tags: [Git, SSH, GitHub, gh, DevOps, Productivity]
categories: [Tool Heroes]
description: "Starting from the most ordinary SSH connectivity-test command, we dig all the way down: GIT_SSH_COMMAND, gh CLI power-moves, multiple accounts on one machine, GitHub Enterprise multi-host, and HTTPS + SAML SSO. Every trap here has been personally stepped on. Copy-paste ready."
---

> It started innocently: a teammate pasted `ssh -i ~/.ssh/id_ed_qan -Tv git@github.com` and asked, "what does this even do?"
> One thing led to another, and we ended up walking through nearly every trap on the Git-connection path.
> So I turned it into this deep dive — **each section gives you the copy-paste answer first, then the why.**

---

## 0. The one-sentence map

This whole post is really nine facets of a single question: **the moment you hit `git clone`, how does your identity actually get verified?**

Bottom to top: SSH handshake → which key → which protocol (SSH vs HTTPS) → how multiple identities on one machine avoid clashing → how an internal GHE layers on top → how to authenticate under SSO. By the end, "why won't it connect?" becomes muscle memory.

---

## 1. The health-check command: `ssh -Tv git@github.com`

**TL;DR: this command tests whether your SSH key can knock on GitHub's door. It clones nothing — pure checkup.**

```bash
ssh -i ~/.ssh/id_ed_qan -Tv git@github.com
```

Breaking it down:

| Part | Meaning |
|---|---|
| `ssh` | the one doing the knocking |
| `-i ~/.ssh/id_ed_qan` | use **this specific** private key (not the default one) |
| `-T` | I don't want an interactive terminal (GitHub gives no shell) |
| `-v` | be verbose, print the handshake so I can troubleshoot |
| `git@github.com` | connect as user `git` to github.com |

On success, GitHub replies with a wonderfully cheeky line:

```
Hi <your-username>! You've successfully authenticated, but GitHub does not provide shell access.
```

**Key point: "does not provide shell access" is NOT an error — it's the success signal.** Plenty of people panic the first time they see it. As long as you see your username, the key worked. Mission accomplished.

---

## 2. Cold facts about `-T` and `-v`

### Capital `-T`: kill the pseudo-terminal

Normally when you `ssh` into a server, SSH requests a terminal so you can type commands. But behind GitHub's door there's **no room** — it gives no shell, so requesting a terminal is like asking thin air for a chair. That's why veterans always add `-T` when connecting to GitHub.

It has an opposite, `-t` (lowercase) = *force* a terminal. Use it on GitHub and you'll see `Pseudo-terminal will not be allocated...` — another line that sounds like an error but isn't.

> Mnemonic: **GitHub → capital T.**

### `-v`: the three chatty brothers

- `-v`: human-readable level. Tells you which config it read, which key it tried, whether the server accepted. **Covers 99% of troubleshooting.**
- `-vv`: adds crypto-algorithm negotiation details.
- `-vvv`: reads every packet aloud, like a play-by-play commentator sitting next to you.

**How to spot which key actually won?** Watch these two lines:

```
debug1: Offering public key: .../id_ed_qan     # I'm trying this one
debug1: Server accepts key: .../id_ed_qan      # this is the one, accepted ✅
```

The filename after `Server accepts key` is the key that took effect. With multiple keys you'll see it `Offering` them one by one, like trying keys on a keyring against a lock.

> Aside: SSH tries at most 6 keys per attempt by default; too many and GitHub slaps you with `Too many authentication failures`. That's the classic "I have the right key but still can't connect" trap — using `-i` to pin one key sidesteps it.

---

## 3. What actually happens during the handshake

`id_ed_qan` is clearly **ed25519** by name (elliptic curve — short, fast, secure; today's default of choice, sweeter than old RSA). It exchanges secret handshakes with GitHub in four steps:

**① Face check (verify the server).** GitHub first shows its own public-key fingerprint: "I'm github.com, this is my face." Your machine flips through `~/.ssh/known_hosts` (its address book) to compare:

- Not in there → prompts `Are you sure you want to continue connecting (yes/no)?`; you type yes and it's saved. **This step is the anti-"fake GitHub" phishing guard** — not a formality.
- In there and matches → passes instantly.
- In there but *doesn't* match → red alarm `REMOTE HOST IDENTIFICATION HAS CHANGED!`, connection refused. Usually GitHub rotated its host key officially (announced), but the mechanism itself is a lifesaver.

**② Show the key (verify you).** You hand over the **public** key matching `id_ed_qan`.

**③ Challenge–response (the crux).** Crucially, **your private key never leaves your machine.** GitHub uses your public key to pose a random puzzle only the matching private key can solve; you solve it locally with the private key and send the answer back; GitHub verifies with the public key: "you answered correctly, so the private key is in your hands." The private key never goes over the wire — that's the magic of asymmetric crypto.

**④ Door opens.** Verified, GitHub says `Hi <username>!` — it recognizes the **username** (when you uploaded the public key, it recorded "this public key = this account"). Then it shows you out. The real `clone`/`push` data flows through this encrypted tunnel.

> In one line: **first I confirm you're the real GitHub (known_hosts), then you confirm I'm really me (private-key challenge), mutual trust established, let's work.**

---

## 4. The classic blunder: `GIT_SSH_COMMAND` meeting an HTTPS URL

Here's a command that **looks clever but silently fails**:

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed_qan" \
  git clone https://github.com/qantasloyalty/edr-airflow-dag-cli.git /tmp/test-edr-cli
```

The intent is clear: clone a repo using a specific key. **But it won't work the way you think.** Two things clash:

- Up front, `GIT_SSH_COMMAND=...` says "when going over SSH, use this key."
- But the URL is **`https://`** — and HTTPS **does not go over SSH at all!**

So that env var is **completely ignored**. It's like clutching a keycard but walking up to a door that wants a password — the card can't beep it open no matter how right it is. HTTPS pulling a private repo wants a **username + token**; it doesn't recognize your SSH private key.

**To make the key take effect, switch the URL to SSH form:**

```
https://github.com/qantasloyalty/edr-airflow-dag-cli.git
        ↓
git@github.com:qantasloyalty/edr-airflow-dag-cli.git
```

Note the two tells: `https://` → `git@github.com`, and the `/` after the domain becomes a **`:`** (the signature mark of an SSH URL).

> Aside: the trailing `/tmp/test-edr-cli` is the target directory; putting it in `/tmp` says "temporary key test, gone on reboot" — a fine choice.

---

## 5. `GIT_SSH_COMMAND` done right

Think of it as **a sticky note you hand git temporarily: "for this command, use this ssh invocation."** It applies only to this one git command and doesn't pollute global settings.

### ① Pin a key temporarily — there's a big trap ⚠️

```bash
# ❌ -i alone sometimes doesn't work
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed_qan" git pull

# ✅ add a "shut-up lock"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed_qan -o IdentitiesOnly=yes" git pull
```

If ssh-agent is running with other keys loaded, ssh will **try the agent's keys one by one first**, pushing the key you pinned to the back — possibly even triggering `Too many authentication failures`. `IdentitiesOnly=yes` means "use only the key I gave with `-i`, don't offer the others." With it, you get true precise key selection.

### ② Skip the host check (emergency/temporary only)

```bash
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" git clone ...
```

The first says "don't ask yes/no, auto-accept new hosts"; the second says "write the verification result to /dev/null — keep no record." Common in CI and throwaway jump hosts.

> 🚨 Serious warning: this **turns off the anti-man-in-the-middle lock** (the "face check" from §3). Only use it when you fully know who's on the other end and the environment is disposable — never on your own long-term machine.

### ③ Debug on the fly

```bash
GIT_SSH_COMMAND="ssh -v" git fetch
```

### It vs `~/.ssh/config` — who wins?

**It's not either/or, it's additive; on conflict, the command line wins.** Because `GIT_SSH_COMMAND` is literally assembling an `ssh ...` invocation, and ssh *always* reads `~/.ssh/config`. The real precedence is the general SSH rule:

> **Command-line args (`-i`/`-o`) > `~/.ssh/config` > `/etc/ssh/ssh_config`**

Translation: the key you pin with `-i` in `GIT_SSH_COMMAND` overrides the `IdentityFile` for that host in config; but settings in config that you **didn't** override (`Port`, `ProxyJump`, `HostName` mapping) still apply. Example: config routes `github.com` through a jump host, and you temporarily swap the key — the result is **still through the jump host + using your temporary key**, each doing its own job.

### Its own three-brother ordering

> **`GIT_SSH_COMMAND` (env var, temporary) > `git config core.sshCommand` (persistent) > the ancient `GIT_SSH`**

Want "this repo always uses a specific key"? Don't retype the env var each time — nail it into the repo:

```bash
git config core.sshCommand "ssh -i ~/.ssh/id_ed_qan -o IdentitiesOnly=yes"
```

---

## 6. The gh CLI's lazy philosophy

**Discovery: `gh auth switch` with no args switches automatically — with only two accounts logged in it silently flips to the other; with three or more it pops a menu.** Behind this is gh's consistent philosophy: **if it can guess what you want, it won't bother you.** More power-moves in the same spirit:

- **`gh pr checkout 1234`** — pull someone's PR to local and run it in one shot; no manual `git fetch` of those refs. A review lifesaver.
- **`gh pr create --fill`** — auto-fill the PR title and body from your commit messages. Add `--web` to open the browser right after creating.
- **`gh browse`** — instantly open the current repo's GitHub page; `gh browse path/to/file.py:42` jumps straight to a file and line — brilliant for sending links.
- **`gh repo clone owner/repo`** — clone without the full URL, and it auto-uses your `gh auth` credentials so you don't sweat SSH vs HTTPS.
- **`gh run watch`** — watch CI/Actions live after pushing; get a notification when it finishes, no page refreshing.
- **`gh api /repos/{owner}/{repo}/issues`** — the nuclear option. Hits any API endpoint carrying your auth; scripting powerhouse.
- **`gh alias set co "pr checkout"`** — save a long command as a short one; `gh co 1234` from then on.

---

## 7. Multiple GitHub accounts on one machine

**First, get clear: you're solving two independent identities — don't conflate them —**

1. **SSH identity**: which key GitHub recognizes when you push/pull (do you have access).
2. **Commit identity**: the `name/email` stamped on the commit (who shows up in the history).

These are independent! Plenty of people get SSH right, then find their work repo full of commits from their personal gmail — cringe. Configure both.

### 7.1 SSH identity: the Host-alias trick

Root problem: two keys, both connecting to the same `github.com`, and SSH can't guess which to use. The fix is to invent **fake domains** in `~/.ssh/config`, each bound to one key:

```ssh-config
# Work account (Qantas)
Host github-qantas
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_qan
    IdentitiesOnly yes

# Personal account
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_personal
    IdentitiesOnly yes
```

- `Host github-qantas` is an **alias you make up** — not a real domain.
- `HostName github.com` is what the alias actually connects to.
- `IdentitiesOnly yes` is the "shut-up lock" — mandatory in multi-account setups.

Then **use the alias in the remote URL** in place of the domain:

```bash
# Work repo
git@github-qantas:qantasloyalty/edr-airflow-dag-cli.git
# Personal repo
git@github-personal:<your-username>/xxx.git
```

For existing repos: `git remote set-url origin git@github-qantas:...`.

> Mnemonic: **the alias distinguishes identity, HostName points at the real server.**

### 7.2 Commit identity: auto-switch by directory

Use `includeIf` in `~/.gitconfig`. Put all work projects under one folder and it auto-stamps the work email:

```ini
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-qantas

[includeIf "gitdir:~/personal/"]
    path = ~/.gitconfig-personal
```

`~/.gitconfig-qantas`:

```ini
[user]
    name = Todd Zhang
    email = todd@qantas.com.au
```

**Effect: a repo under `~/work/` stamps the work email; under `~/personal/` stamps the personal one.** Directory = identity, no manual toggling.

> ⚠️ Trap: don't drop the trailing `/` in `gitdir:`; it matches the repo's directory.

---

## 8. GitHub Enterprise + multi-host

Scenario: public `github.com` (open source / personal) and a company-hosted **GitHub Enterprise** (internal) coexisting on one machine.

**The mindset: GHE and github.com are two completely different servers, not just two accounts — you layer "multi-account" on top of "multi-host," and configure SSH and gh separately.** GHE has its own domain, e.g. `github.qantas.com.au`.

### 8.1 SSH: stack three Host blocks

Building on §7, add one more:

```ssh-config
Host github-qantas          # public work account
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_qan
    IdentitiesOnly yes

Host github-personal        # public personal account
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_personal
    IdentitiesOnly yes

Host ghe                    # internal GitHub Enterprise
    HostName github.qantas.com.au   # ← swap for your real GHE domain
    User git
    IdentityFile ~/.ssh/id_ed_ghe
    IdentitiesOnly yes
```

Corresponding URL: `git@ghe:team/some-repo.git`.

**Two GHE-specific traps:**

1. **Different known_hosts fingerprint.** The first connection re-does the face check (normal — it's a different server). If you hit `REMOTE HOST IDENTIFICATION HAS CHANGED`, don't rush to delete known_hosts — check with your platform team whether it's an official rotation or a real problem.
2. **May use a non-standard port or a jump host.** Add `Port <port>` or `ProxyJump <jump-host>` to that Host block, and `git@ghe:...` picks it up automatically.

### 8.2 gh CLI: one tool, two hosts

gh **natively supports multiple hosts**:

```bash
gh auth login                                  # defaults to github.com
gh auth login --hostname github.qantas.com.au  # internal GHE
gh auth status                                 # lists both hosts together
```

Key rule: **gh commands default to github.com only**; to act on GHE, name it:

```bash
gh repo list --hostname github.qantas.com.au   # one-off
export GH_HOST=github.qantas.com.au            # switch for the whole session
```

> Don't mix the two axes: **host is "which server" (`--hostname`/`GH_HOST`); `gh auth switch` is "which person on that server."**

### 8.3 Cheat sheet

| Axis | Public github.com | Internal GHE |
|---|---|---|
| SSH alias | `github-qantas` / `github-personal` | `ghe` |
| Real domain | github.com | github.qantas.com.au |
| gh login | `gh auth login` | `gh auth login --hostname ...` |
| gh switch | same host → `gh auth switch` | switch host → `GH_HOST`/`--hostname` |
| Commit identity | by directory via `includeIf` | same, usually the work email |

---

## 9. HTTPS + SAML SSO: a world without SSH

Scenario: the company disables SSH, allows only HTTPS, and wraps it in SAML single sign-on.

**The core: there's no SSH key anymore — your "key" becomes a Personal Access Token (PAT); and the biggest SSO trap is that creating the token isn't enough — you must also "stamp an org authorization" on it, or accessing org repos throws a bewildering 404.**

### 9.1 Why HTTPS + Token

SSH disabled → HTTPS only → private repos need auth → GitHub long ago stopped allowing account passwords → use a **PAT** (scoped permissions, an expiry, individually revocable).

- **Classic:** one token spans all your repos, permissions checked by broad category (`repo`, `read:org`, `workflow`).
- **Fine-grained:** scoped to specific repos, read-only, etc. More secure; big companies often mandate it.

### 9.2 That SSO "stamp" trap (where 90% of people get stuck) ⚠️

After you create the token, it **can access personal repos, but the moment it touches an org repo → 404 or "SAML SSO required."** Many people assume permissions are wrong and fiddle for ages — wrong direction entirely.

The truth: the token is **not authorized for that org** by default. Go to the token settings page, click **"Configure SSO" → Authorize** for the target org next to that token. Once stamped, access works.

> 💡 Author's-view cold fact: why **404 and not 403**? Returning 403 ("forbidden") would tacitly admit "this private repo exists, you just lack access" — leaking whether the repo exists. GitHub deliberately returns 404 ("nothing here") to prevent that info leak. **So in an SSO context, a baffling 404's first suspect should be "token not authorized for the org," not "wrong path."**

### 9.3 Easiest path: let gh handle everything

Wiring up git's credential helper by hand is tedious — just use `gh`:

```bash
gh auth login --hostname github.qantas.com.au   # choose HTTPS; browser OAuth completes SSO authz too
gh auth setup-git                                # register the token as git's credential helper
```

The second line is the key magic: afterward, plain `git clone https://...` / `git push` will have git fetch the token from gh automatically — **no more typing it by hand.**

### 9.4 Token minimal scopes & survival notes

Keep it lean: `repo` (read/write repos), `read:org` (many gh commands need it), `workflow` (only if touching Actions).

Three survival rules:
- **Set an expiry** — no never-expiring tokens (a time bomb).
- **Never hardcode into code or `.git/config`** — hand it to gh / the OS credential manager (macOS Keychain, Windows Credential Manager).
- Suspect a leak → **Revoke** on the settings page and recreate. That's exactly where a token beats a password.

### 9.5 One-line selection

| Scenario | Pick |
|---|---|
| Company disables SSH / has SSO | HTTPS + Token |
| Your own machine, SSH allowed | SSH key (set once, no expiry chasing) |
| CI/CD pipeline | Token / deploy key / Actions' built-in `GITHUB_TOKEN` |

---

## Wrap-up: a troubleshooting mind map

When it won't connect / uses the wrong identity, check these three layers top-down:

1. **Right protocol?** Is the URL `git@...` (SSH) or `https://...` (HTTPS)? The two paths want completely different credentials (§4).
2. **Right identity?**
   - SSH: `ssh -Tv git@<alias>` and check whether `Server accepts key` is the one you want (§2, §7); for multi-account, confirm the remote uses the alias.
   - HTTPS/SSO: for a 404, first suspect "token not authorized for the org" (§9).
3. **Right commit identity?** Glance at one of your own commits — is the email the right account's (§7.2)?

Turn these three layers into muscle memory and you'll self-diagnose almost any GitHub-connection issue within five minutes.

> The end. Stepped on a trap I missed? Come tell me and I'll add it 😎
