---
title: The PID You Watch Is Not the PID That Works — PM2 + uv + interop
header:
    image: /assets/images/hd_containers.png
date: 2026-11-05
tags:
 - devops
 - debugging
 - wsl
 - pm2
 - reliability
permalink: /blogs/tech/en/pid-you-watch-vs-pid-that-runs
lang: en
layout: single
category: tech
---

> You can't manage what you don't measure — but it's more dangerous to measure something you *think* is the thing, and isn't.

# Your gateway crash-looped 865 times. It never actually restarted.

*From "the process is supervised" to "the supervised one is the one that runs" — a post-mortem that crosses the WSL / Windows boundary.*

This is a sequel to [`max_restarts is not a restart budget`](/blogs/tech/en/pm2-max-restarts-is-not-a-budget). Same `ecosystem.wsl.config.js`, same PM2 — but this time the trap isn't in the config's *semantics*. It's in the *process the config points at*: the PID I was watching was never the PID doing the work.

The trigger was mundane. My MCP gateway — a long-running HTTP service bound to `127.0.0.1:8800` — showed up in the failure list again. Here's what `pm2 list` told me:

```
│ id │ name        │ status │ restarts │ uptime │
│ 1  │ mcp-gateway │ online │ 865      │ 16s    │
```

865 restarts, up for 16 seconds. A textbook crash-loop. My reflex was to go dig logs and hunt for a port conflict.

But before touching anything, I asked one more question, and curled the service's own health endpoint:

```bash
$ curl -s http://127.0.0.1:8800/health
{"status":"ok","uptime_s":16187, ...}
```

**`uptime_s: 16187`. Four and a half hours.**

One process. PM2 says it's been alive for 16 seconds and died 865 times. It says it's been running for 4.5 hours straight. Both cannot be true — *unless the process PM2 is watching and the process answering my curl are not the same process at all.*

This post is about that crack: why it opens, how to chase it across an operating-system boundary, and why the only real fix is one sentence — **make the thing you supervise be the thing that runs.**

## What you'll walk away with

- **An instinct for spotting a ghost process**: when a service reports two contradictory "ages," don't reconcile them — go count how many processes there actually are.
- **A claim you can push back on**: `uv run` is a fine dev-time tool, but putting it in the `script` slot of any long-lived process supervisor is almost always manufacturing orphans.
- **A map for tracing process ancestry across the WSL / Windows boundary**, plus what interop actually is and why it's both the convenience and the cause of split-brain.

Ordered most-useful-first, not in my actual debugging order — no need to walk you through the detours I took.

---

## 1. A process can't have two ages

The first-principles question in any debug isn't "what's broken." It's "of these two signals in my hand, which one describes the thing I actually care about?"

Put the two numbers side by side:

| Signal | What it says | Who it describes |
|---|---|---|
| `pm2 list` → `uptime 16s`, `restarts 865` | A process that suicides every 15s | **The process PM2 forked itself** |
| `/health` → `uptime_s 16187` | A service alive for 4.5h straight | **The process actually bound to :8800, serving requests** |

Neither signal is lying. They describe **two different processes**. PM2 is monitoring something that's endlessly reborn and dying; the thing actually serving me is a different process it's never heard of — one that escaped to the background and has lived there for 4.5 hours.

> When one entity reports two values that can't coexist, the answer is almost never "one of them is wrong." It's "the one you thought it was is actually two."

That's the spine of this post. I'll give it a name: **supervision alignment.** Every bit of value a process supervisor (PM2, systemd, supervisord…) can offer rests on one contract — **the PID it watches must be the PID that actually works.** Break that contract and everything the supervisor reports — status, restart count, CPU, memory — describes a ghost.

And this contract breaks two ways. Here's the first.

---

## 2. Vertical misalignment: the `uv run` double-fork orphan

In my `ecosystem.wsl.config.js`, the gateway block originally read:

```js
{
  name: "mcp-gateway",
  script: "uv",
  args: "run python gateway.py",
  cwd: "~/ws/project/ai/mcp/gateway",
}
```

Looks obvious — run Python via `uv`, let uv handle the env and deps. But stare at one question: *who exactly did PM2 spawn?*

PM2's supervision model is dead simple: it `spawn`s a child, **records that child's PID**, then watches that PID's liveness, signals that PID, and counts restarts against that PID. Everything is bound to "the PID it forked itself."

And `uv run python gateway.py` actually does this:

```
PM2 spawn ──► uv (PID 1654)          ← PM2 thinks "app = 1654", watches it
                 │  uv prepares the env (locates venv, syncs deps, sets PATH)
                 └──► python3 gateway.py (PID 3841)   ← THIS is what binds :8800
```

`uv run` **does not exec-replace itself.** It spawns a subprocess to run your command and stays on top as the parent. So there are always two layers: `uv(1654)` as parent, `python(3841)` doing the work. PM2 knows 1654; :8800 is held by 3841.

The misalignment is now baked in. Any restart detonates it:

| Step | What happens |
|---|---|
| 1 | PM2 wants to restart → sends SIGTERM to the PID it recorded, 1654 (uv) |
| 2 | uv dies, but child 3841 (python) **does not die with it** — it's reparented to PID 1, now an **orphan**, still clutching :8800 |
| 3 | PM2 sees 1654 gone → declares the app dead → `spawn`s a new uv → new uv launches a new python |
| 4 | The new python tries to bind :8800 → **`EADDRINUSE`** (orphan 3841 holds it) → crashes instantly |
| 5 | PM2 declares it dead again → restart → hit the orphan again → **infinite crash-loop** |

That's how you burn 865 restarts. And the `/health` that claimed "4.5 hours" is that very orphan from step 2 — the first one to escape, never killed — still answering. The two-ages mystery closes here.

> A "double fork" is the classic trick a daemon uses *on purpose* to detach from its parent and attach to init. `uv run` isn't deliberately daemonizing, but that one layer of "wrapper → subprocess" reproduces the exact same effect: the grandchild that actually matters escapes the supervisor's line of sight and signal range.

**The naive take:** uv run works fine, the service starts fine by hand, so the config is fine.
**The seasoned take:** "works by hand" and "works under a supervisor" are different claims. By hand, *you* are the parent and you can see the child. Under supervision, the *supervisor* is the parent, and all it can see is the uv shell.

The fix is two lines — make PM2 spawn the real interpreter directly:

```js
{
  name: "mcp-gateway",
  script: ".venv/bin/python3",   // was "uv"
  args: "gateway.py",            // was "run python gateway.py"
  cwd: "~/ws/project/ai/mcp/gateway",
}
```

`.venv/bin/python3` is already this venv's interpreter — the deps and site-packages live inside it, so there's no need for uv to wrap it at runtime. uv's value is **installing and locking deps at dev time**, not **keeping a process resident in production**. Pick the right layer and the misalignment vanishes.

After the change, I ran an alignment check:

```bash
$ port owner pid = 41960
$ PM2 recorded pid = 41960   ✅ match
```

**What PM2 watches is what holds the port.** The contract holds for the first time. Which is my first stance: **putting `uv run` in the `script` slot of PM2 / systemd is almost always wrong — it's a dependency installer, not a process runtime.**

---

## 3. Interlude: what interop is, and how it let a second supervisor sneak in

Having fixed the vertical misalignment, I thought I was done. Then the port got stolen again. Chasing the culprit forced me to finally understand a WSL primitive down to the metal — **interop.** Get this straight first, or chapter 4's "horizontal misalignment" won't parse.

**Interop (Windows-Linux interoperability) is the ability of WSL2 and Windows to invoke each other's executables.** It's bidirectional:

- From inside WSL (Linux), you can type `powershell.exe`, `schtasks.exe`, `wsl.exe` — real **Windows `.exe`s** — and they actually run on the Windows side, piping output back to your Linux terminal.
- The other way, Windows can run `wsl.exe -d Ubuntu -- <command>` to reach into Linux.

Why does typing `powershell.exe` inside Linux "magically" work? The kernel's **`binfmt_misc`** mechanism: it registers a rule — "see a `.exe`, hand it to a process called `/init`, which forwards it to Windows." That `/init` is interop's **boundary translator.**

Remember chasing a process ancestry with `ps`, climbing up, and suddenly hitting a wall of `/init`? That's not a broken process tree — **that's you hitting the OS boundary marker.** `/init` means: the real originator of this process isn't on the Linux side. It's on Windows.

> This is what I call **information directionality**: every context boundary (host↔guest, frontend↔backend, ORM↔SQL) rewrites information according to its own side's assumptions. Cross the `/init` boundary and Linux's `ps` can no longer see upstream — the semantics still exist, but you have to switch to the tool on the other side (Windows's process table) to read them.

Hold onto this: **when a process chain hits `/init`, switch to the Windows side to keep chasing.** That's exactly how chapter 4 cracks the case.

---

## 4. Horizontal misalignment: two PM2s on one machine

The port was stolen again, but the WSL-side PM2 was demonstrably clean. I traced the ancestry of the :8800 owner:

```
python3 gateway.py (holds :8800)
  ← uv run --directory ~/ws/project/.../gateway python gateway.py
      ← /init        ← hit the boundary! the originator is on Windows
```

Per chapter 3's lesson, switch to the Windows side. From inside WSL I called `powershell.exe` to query the Windows process table for anything with `gateway` in its command line:

```powershell
ProcessId   : 24040
Name        : wsl.exe
CommandLine : "C:\Program Files\WSL\wsl.exe" -d Ubuntu -u <you> --
              zsh -lc "... exec uv run --directory
              ~/ws/project/ai/mcp/gateway python gateway.py"
```

A `wsl.exe` on Windows, reaching back into WSL to launch my gateway. So who's *its* parent? Keep climbing:

```
wsl.exe (24040)
  ← node  ...\pm2\lib\ProcessContainerFork.js  (PID 45564)   ← a PM2 app's worker
      ← node  ...\pm2\lib\Daemon.js            (PID 70044)   ← the PM2 daemon itself
```

There it is: **the "Windows-side launcher" was never some mystery task. It's a second PM2 — just installed on Windows.**

This machine has **two PM2s.** I listed the apps on the Windows one:

```
name              pm_id  restart_time
toddy-portal      0      0
mcp-gateway       1      99     ← reaches into WSL via launcher.js → wsl.exe, holds :8800
bank-chatbot-api  2      156
portal-api        3      2693   ← crash-looping hard, can't grab :8002
```

It runs an entire stack **nearly duplicating** the WSL side. Two supervisors, each convinced it owns these ports, so they fight forever:

| | WSL PM2 | Windows PM2 |
|---|---|---|
| Thinks it manages | gateway + three others | gateway + three others |
| Who actually owns :8800 | loses, crash-loops | won this round, holds it |
| Who actually owns :8002 | won it | loses → portal-api restarts 2693× |
| Symptom | random cross-session crashes | silently burning CPU in the background |

This is **horizontal misalignment**, a.k.a. split-brain: two supervisors holding near-identical app lists, racing for the same resources. Whoever starts first binds; the other crash-loops forever. It's sneakier than the vertical kind — because **one of them always appears to be running fine**, and the whole cost hides in the background churn.

```
★ Why interop is the accomplice ──────────────
Precisely because interop is bidirectional, the Windows PM2 can
reach back into WSL via wsl.exe and grab ports. Without interop,
the two OSes' processes mind their own business and split-brain
simply can't form. Interop is double-edged: it removes the
friction of "run a command across OSes" and removes the clear
boundary of "who manages what" in the same stroke.
──────────────────────────────────────────────
```

Fixing horizontal misalignment takes the same single principle as vertical: **one service, one supervisor.** I chose to let WSL PM2 own everything (which is the whole point of "unified management inside WSL"), so I deleted all four apps from the Windows PM2:

```powershell
pm2 delete all
pm2 save --force
```

`delete` stops and removes them; `save --force` wipes them from the resurrect-on-boot list so they won't come back after a restart. That CPU-burning `portal-api` with 2693 restarts vanished along with them.

> My second stance: **a service managed by two supervisors is worse than one managed by zero.** With zero, you know the instant it dies. With two, it always "looks alive," and you never know whose reading to trust.

---

## 5. Stitching the two misalignments together

The two culprits here look nothing alike — one's a process wrapper, one's a second daemon across an OS boundary — but they commit the **same error**:

| | Misalignment is between | Supervisor watches | What actually works | Fix |
|---|---|---|---|---|
| **Vertical** (uv orphan) | parent/child layers inside one process | the uv wrapper (1654) | the python interpreter (3841) | make PM2 spawn the interpreter directly |
| **Horizontal** (split-brain) | two supervisors across two OSes | the copy each one thinks it owns | whichever actually grabbed the port | cut down to a single supervisor |

Two misalignments, one spine: **supervision alignment.** Vertical is "the layer you manage isn't the layer that works"; horizontal is "you're not the only one managing it." Whenever "manage" and "run" aren't strictly one-to-one, every reading the supervisor hands you describes a ghost.

Which connects right back to the previous post. That one was about the instrument's *semantics* deceiving you (`max_restarts` is a time window, not a count). This one is about the instrument watching the wrong *object* (the PID it watches isn't the PID that works). The first is "someone rescaled the bathroom scale"; the second is "you're weighing a different person entirely." Put together, they're one sentence:

> For a health check to be trustworthy, it has to measure the right **quantity** *and* the right **thing**.

---

## What you can do today

1. For every service you run under PM2 / systemd, do an **alignment check**: does the `PID the supervisor recorded` equal the `PID actually bound to the port` (`ss -ltnp` shows the owner)? If not, you're supervising a ghost.
2. Pull up your ecosystem / service files and check whether the `script` slot is a **wrapper** — `uv run` / `npm run` / `poetry run`. If so, replace it with the real executable it ultimately execs (`.venv/bin/python3`, `node`, the concrete binary).
3. When a service reports **two contradictory "ages" or statuses**, don't reconcile the numbers — `pgrep -af <name>` and count how many processes there really are. The ghost hides in the count.
4. If you use both WSL and Windows: run `pm2 list` on **both** sides (Windows side: `powershell.exe pm2 list`). Confirm the same service isn't owned by two PM2s at once.
5. Learn one tracing move: the moment `ps` hits `/init` while climbing, switch to the Windows side with `powershell.exe Get-CimInstance Win32_Process` and keep going. `/init` isn't the end — it's the boundary.

---

*All a supervisor can ever tell you is "the one I'm watching is still there." The sentence it can't say — "am I watching the right one?" — is the one you're on the hook to answer yourself.*
