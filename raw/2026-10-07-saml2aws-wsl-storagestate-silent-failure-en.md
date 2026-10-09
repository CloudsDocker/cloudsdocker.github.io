---
title: Why saml2aws Re-Prompts Every Login on WSL — A Silent storageState Bug
header:
    image: /assets/images/hd_aws_certificat.png
date: 2026-10-07
tags:
 - aws
 - wsl
 - saml2aws
 - debugging
 - sso
permalink: /blogs/tech/en/saml2aws-wsl-storagestate-silent-failure
layout: single
category: tech
---

> The most dangerous kind of waste is the waste nobody recognizes. — Shigeo Shingo

# The Login That INFO Swallowed

*How one missing `os.MkdirAll` quietly cost every fresh install an extra login — and sat unfixed for 18 months*

## The incident

On my Mac, `saml2aws login` had been a pleasure for a long time: log into Google SSO once in the popup browser, and every run after that sailed straight through to AWS credentials in a couple of seconds.

I moved the exact same setup to WSL2 and it turned into a different animal. **Every single** `saml2aws login` opened Chromium and made me type my Google email, my password, and clear MFA from scratch. Same config file. Same tool version (`saml2aws 2.36.19`). So why does the Mac remember and WSL forget?

My first instinct — probably yours too — was wrong:

> "WSL just isn't saving the login to a keyring, right? Linux has no macOS Keychain, so the password has nowhere to live, so it asks every time."

It's a very reasonable instinct. It also cost me a solid ten minutes down a dead end.

If you've ever hit "same tool, remembers my login on one machine, stubbornly forgets on another," this is the trail for you. You'll walk away with three things:

- a method for deciding *where persistence actually lives* — **don't guess; trace where the data is supposed to be written**;
- a way to pin down the nastiest class of bug, "the command succeeded but a side effect silently failed";
- and a lesson more expensive than the bug itself: **the cost of an error has nothing to do with its severity level.**

I'm telling this in most-useful-first order, not the order I actually tripped over it — I spent ten real minutes on the keyring dead end, and I'm sparing you that leg.

## 1. The wrong first instinct: this is not a keyring problem

I went to confirm the "keyring isn't saving the password" theory first. And sure enough, WSL had no working secret-service: `secret-tool` not installed, `GNOME_KEYRING_CONTROL` empty, no gnome-keyring daemon running. The evidence lined up. The theory looked solid.

One detail blew up the whole chain of reasoning — my config said:

```ini
# ~/.saml2aws
provider = Browser
```

`provider = Browser` means **the thing that actually logs me into Google is the SSO flow in the browser**, not the password I type in the terminal. That terminal Username/Password prompt (and its little "To use saved password just hit enter") is basically vestigial in Browser mode. Which means: **whether or not the keyring stores a password has zero effect on whether the browser makes me log in again.**

| The naive read | The seasoned read |
|---|---|
| Asks for my password every time = password not saved = keyring broken | Check `provider` first. In Browser mode auth happens in the browser; the terminal password is a prop |
| macOS has Keychain, Linux doesn't, so behavior differs | Both run the same code. The difference must be in *the thing that code reads and writes* on each OS |

**Broken symmetry**: when two machines run the same binary with the same config but behave differently, the difference isn't in the code — it's in the *external state the code depends on*. I wasn't looking for "which branch differs." I was looking for "which file or directory exists on one box and not the other."

> Same code, different behavior: the difference is always in the ground it reads and writes, not in the code.

## 2. The second pivot: persistence doesn't live in the browser profile

If auth happens in the browser, then "remembering the login" means "the browser kept Google's session cookie." So I went digging on disk for the user-data directory saml2aws hands to Chromium. What I found was this:

```text
/tmp/playwright_chromiumdev_profile-DGdPIX/Default/Cookies
```

Look at that random suffix, `-DGdPIX`. That's the name Playwright gives a **throwaway, ephemeral profile** — used once, discarded, fresh one every launch. So saml2aws's Browser provider (playwright-go underneath) spins up a clean temporary browser every time.

Which raises the obvious question: if the browser profile is disposable, how does the Mac "remember" anything?

The answer: **the real persistence doesn't live in the browser profile at all.** That was the turning point. Instead of guessing further, I read the source and found out exactly where the session goes.

## 3. First principles: read the source, stop guessing

I opened `pkg/provider/browser/browser.go` in `saml2aws` v2.36.19. The mechanism became obvious — it uses Playwright's **storage state**: the browser profile is ephemeral, but the cookies + localStorage from a login are exported to a side-car JSON file and injected back into a brand-new context next time:

```go
storageStatePath := fmt.Sprintf("%s/.aws/saml2aws/storageState.json", userHomeDir)
```

The bug is in how it uses that path. Three snippets, and the whole thing assembles:

```go
// 1) Loading is conditional: only read if the file already exists
if _, err := os.Stat(storageStatePath); err == nil {
    contextOptions.StorageStatePath = playwright.String(storageStatePath)
}

// 2) Before saving, there is no os.MkdirAll anywhere — it never creates the dir

// 3) A failed save is logged at INFO and swallowed
_, err := context.StorageState(storageStatePath)
if err != nil {
    logger.Info("Error saving storage state", err)
}
```

**Code archaeology**: three months from now nobody will remember why the Mac worked and WSL didn't, because the answer was never in an error — only in one INFO line nobody reads. Reading the source took five minutes, and was faster and more certain than the ten I'd burned guessing at keyrings.

> When a succeeding command hides a silently-failing side effect, the log level is your only clue — and here it was turned down to the quietest setting.

## 4. Root cause and a one-line fix

Line up those three snippets against the actual state of my WSL box and the loop closes:

```text
~/.aws/saml2aws/            ← the whole directory doesn't exist
~/.aws/saml2aws/storageState.json   ← so it is never created
```

Every login was therefore: **dir missing → nothing to load (os.Stat fails) → full login + MFA → try to save, fail because the dir is missing → failure demoted to an INFO line and swallowed → file never created → next run starts from zero.**

The *only* reason the Mac was smooth is that the directory got created there at some point — once `storageState.json` exists, the loop sustains itself. The difference was never an OS capability. It was the presence of one directory.

The fix is one line:

```bash
mkdir -p ~/.aws/saml2aws
# then log in once more (this time it fully logs in AND successfully writes storageState.json)
saml2aws login --profile <your-profile>
# verify the file actually appeared
ls -la ~/.aws/saml2aws/storageState.json
```

After that, every login skips the Google prompt like the Mac does, until Google's session cookie expires (typically days to weeks).

**The WSL second-order trap (worth interview points)**: if, on WSL, you've symlinked `~/.aws` onto the Windows drive —

```text
~/.aws  ->  /mnt/c/Users/<you>/.aws     (drvfs mount)
```

— then even with the directory created, writing `storageState.json` can be flaky due to drvfs file-locking / atomic-write quirks. If you hit that, put `~/.aws` (or just a dedicated saml2aws path) on the WSL-native filesystem and sidestep drvfs entirely. Neither of the two existing upstream fix PRs covers this.

## 5. The lesson that costs more than the bug: cost = observability × frequency

This is the one counter-intuitive takeaway I want you to leave with.

That missing `os.MkdirAll` is not some deep bug. It's an obvious oversight you grasp at a glance. But its **cost** is wildly underrated, because we habitually rank bugs by *severity level* — a crash is P0, an INFO line is "meh." That ranking is wrong.

What actually sets the cost is the product of two things:

- **Observability**: how hard is the failure to notice? (crash: instantly visible; one line in an INFO log: effectively invisible)
- **Frequency**: how often does it happen? (this bug: every fresh install, every login)

A crash gets fixed fast because it's loud. This save-failure, demoted to INFO, quietly makes **every** fresh Browser-provider user redo MFA on **every** login — and nobody knows session persistence is even broken.

This isn't my speculation. One look upstream tells you how expensive it is:

| Signal | Reality |
|---|---|
| Was the bug reported? | Yes — issue **#1526**, title almost word-for-word my conclusion |
| Is there a fix? | **Two** PRs (**#1522**, **#1527**), each adding one `os.MkdirAll` |
| Were they merged? | No. Sitting 4–7 months, zero review |
| Is this an obscure project? | ⭐ 2,246, **295 open issues**, last release **18 months ago** |

A one-line correct fix, sitting for most of a year in a 2k-star tool with nobody merging it. Not because it's hard — because it's never loud. **Nobody was ever woken up by it.**

**Tribal knowledge → engineered artifact**: this is exactly the Senior/Principal dividing line. A Senior knows "just `mkdir` it," fixes their own box, and moves on — that knowledge lives in their head; it's tribal. A Principal asks: why should every new user have to rediscover this? So that fix becomes an `os.MkdirAll` in the code, becomes an *explicit error* on save failure (not an INFO line), becomes one sentence in the README. **Turning what only survives by word of mouth into code, docs, or a check — that's the Principal's job.**

> The most dangerous waste is the waste you never notice. The lower the log level, the longer that waste survives.

## Three maps

Collapse the whole hunt into one sentence: I wasn't chasing a bug, I was chasing the data-flow question "where does persistence actually land?"

| Where I thought persistence lived | Where it actually lives | Why I guessed wrong |
|---|---|---|
| keyring (the password vault) | nothing to do with it | misled by "Linux has no Keychain" |
| browser profile (cookie in the browser) | a temp dir, used once | assumed "remember login" = browser keeps the cookie |
| — | a side-car `storageState.json` (but the dir is never created) | the truth was only in the source, not in any error |

## Do this today

1. If you use `saml2aws` Browser provider and re-login every time: `mkdir -p ~/.aws/saml2aws`, log in once more, confirm `storageState.json` appears.
2. Drop a "reproduced on WSL2 + v2.36.19" on issue **#1526** and an LGTM on **#1522 / #1527** — pushing a correct fix over the line in an under-maintained-but-useful tool is worth more than opening yet another duplicate PR.
3. Audit your own `logger.Info("...failed...", err)` calls: did you demote some *failure* to INFO? Re-rank it by observability × frequency, not by how severe it *feels*.

## Next up

This bug nudged me toward another idea: since the Browser-provider path (real-browser SSO) is where things are heading, and the original is clearly unmaintained here — **if I were to rewrite that path, how should session persistence be done right?** Auto-refresh, expiry awareness, multi-account session management, WSL-first ergonomics. That's the next post.

---

*A tool "running" is not a tool "doing it right." It just turned the failure's volume down, and waited for the day you switch machines to make you finally hear it.*
