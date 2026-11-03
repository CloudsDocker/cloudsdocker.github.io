---
title: "CUI ? GUI? pm2 Spawning Endless Terminal Windows on Windows? It's Not a Config Problem — It's the EXE's PE Header"
header:
    image: /assets/images/hd_nodejs_faq.png
date: 2026-10-31
tags:
 - devops
 - python
 - windows
 - fastapi
 - debugging
permalink: /blogs/tech/en/pm2-windows-crash-loop-pythonw
lang: en
layout: single
category: tech
---

> "The problem is never the one you see." — Richard Feynman

# Your pm2 Apps Keep Popping Terminal Windows on Windows — Stop Blaming pm2

*From a port conflict to a PE header flag — a three-layer debug that reveals how Windows really spawns processes*

6:30 PM on a Friday. I ran `pm2 start ecosystem.config.js` on my toddy_portal project and my desktop exploded.

Black terminal windows erupted like popcorn — one per second, stacking on the taskbar faster than I could close them. My first thought: pm2 is broken. My second thought: malware. Both wrong.

Here's what you'll walk away with:

- **Why pm2's crash-loop is invisible on Linux but a visual catastrophe on Windows** — and it's not pm2's fault
- **Why `windowsHide: true` won't save you** — and what actually will
- **A copy-paste `restartGuard` template** that prevents restart storms on any platform

## 1. Layer One: A Port Conflict Triggers an Infinite Restart Loop

The pm2 error log was screaming the same line over and over:

```
ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8002):
       [winerror 10048] only one usage of each socket address
       (protocol/network address/port) is normally permitted
```

Simple cause: an earlier ad-hoc `python -m portal_api.main` was still holding port 8002. Uvicorn starts → bind fails → process exits → pm2 restarts immediately → fails again → restarts again…

| Setting | Default | Consequence |
|---|---|---|
| `autorestart` | `true` | Restart on any exit |
| `max_restarts` | Unlimited | Never gives up |
| Restart delay | 0ms | One attempt per second |
| Time from exit to new window | ~100ms | A new console window each time |

On Linux this is a silent problem — child processes share the parent's terminal, no new windows pop up. You'd notice the restart counter climbing in `pm2 ls` eventually. On Windows, every restart spawns a visible console window. An infinite loop becomes an infinite stream of flashing black rectangles.

> The same config line can mean completely different things on different operating systems. Before debugging a behavior, ask: do I actually understand what this line does on *this* platform?

## 2. Layer Two: Why Every Restart Opens a Window — the Windows Console Subsystem

I killed the rogue process. The crash-loop stopped. Both Python services came up and stayed up.

But the windows stayed too.

Two black terminals sat on my desktop — one for `portal-api` (port 8002), one for `bank-chatbot-api` (port 8001). Close one? pm2 thinks the service crashed, restarts it, and the window comes right back.

This is where it gets interesting.

Every Windows executable (PE format) carries a `Subsystem` field in its file header:

| PE Subsystem | Value | Behavior |
|---|---|---|
| `IMAGE_SUBSYSTEM_WINDOWS_CUI` | 3 | **Console app** — Windows *must* allocate a console window |
| `IMAGE_SUBSYSTEM_WINDOWS_GUI` | 2 | **GUI app** — no console window created automatically |

`uv.exe`, `python.exe`, `cmd.exe` — all CUI. When pm2 (a node process) spawns them via `child_process.spawn`, Windows sees the child needs a console but the parent may not have one to share, so it **creates a new one**. Every. Single. Time.

This isn't a pm2 bug. It's a `CreateProcess` rule baked into the OS: **a CUI process without an inheritable console always gets a new one.**

What about pm2's `windowsHide: true`? It's supposed to pass `CREATE_NO_WINDOW` in the `dwCreationFlags` to `CreateProcess`. In practice, when `interpreter: "none"` is set (direct exe execution), the flag doesn't get reliably forwarded. Whether this is a pm2 fork-mode issue or a node `child_process` Windows behavior gap, the result is the same: **`windowsHide` is unreliable for this use case.**

> Interview-grade insight: if someone asks "why does a process pop a terminal window on Windows," the answer is the PE header's Subsystem field — not system settings, not console properties. It's decided at compile time, baked into the binary.

## 3. Layer Three: The Real Fix — pythonw.exe

Python ships two executables in every installation:

| File | Subsystem | Window | Capability |
|---|---|---|---|
| `python.exe` | CUI (Console) | Always creates one | Full Python interpreter |
| `pythonw.exe` | GUI (Windows) | Never creates one | **Identical** Python interpreter |

The difference is **one field** in the PE header. Everything else — script execution, module loading, uvicorn, pip — works identically. And pm2 captures stdout/stderr through pipes, not through the console, so logging is completely unaffected.

### Before

```js
{
  name: "portal-api",
  script: "C:\\...\\uv.exe",                    // CUI → window
  args: "run uvicorn portal_api.main:app --host 127.0.0.1 --port 8002",
  interpreter: "none",
}
```

### After

```js
{
  name: "portal-api",
  script: path.join(__dirname, "services", "portal_api",
                    ".venv", "Scripts", "pythonw.exe"),  // GUI → no window
  args: "-m uvicorn portal_api.main:app --host 127.0.0.1 --port 8002",
  interpreter: "none",
}
```

Windows gone. pm2 logs, health checks, traffic proxying — all working perfectly.

## 4. The restartGuard Template — Copy This

Regardless of whether you use pythonw, add restart guards to every pm2 app. This turns a crash-loop from "infinite storm" into "tries a few times, then stops":

```js
const restartGuard = {
  autorestart: true,
  min_uptime: "10s",                  // Exit within 10s counts as crash
  max_restarts: 5,                     // Give up after 5 crashes
  exp_backoff_restart_delay: 2000,     // Backoff: 2s → 4s → 8s → 16s → 32s
  windowsHide: true,                   // Best-effort
};
```

| Parameter | Without it | With it |
|---|---|---|
| `min_uptime` | Any exit triggers restart | Only exits within 10s count toward the limit |
| `max_restarts` | Infinite | 5 attempts, then status → `errored` |
| `exp_backoff_restart_delay` | 0ms | Exponential backoff, maxing ~30s |

Even on Linux, a naked pm2 crash-loop eats CPU and explodes log files. Adding guards is basic hygiene.

## The Full Debug Path

| Layer | Symptom | Root Cause | Fix |
|---|---|---|---|
| 1. Crash-loop | Windows spawning wildly | Port 8002 occupied → uvicorn bind fails → pm2 infinite restart | Kill the rogue process + add restartGuard |
| 2. Persistent windows | Services stable but desktop has two black terminals | `uv.exe` is CUI subsystem → Windows must allocate a console | Recognize `windowsHide` is unreliable |
| 3. Root fix | — | PE header Subsystem determines everything | Use `pythonw.exe` (GUI subsystem) instead of `uv.exe` |

> First principles: don't patch system-level behavior at the application layer. Windows allocating a console for CUI processes is an OS-level invariant — if you want to bypass it, you can't keep standing on CUI ground. Switching to a different Subsystem is speaking the OS's own language.

## Things You Can Do Right Now

1. **`grep -r 'interpreter.*none' ecosystem.config.js`** — check if you're directly executing any `.exe` in pm2 on Windows. If so, check what subsystem that exe is.
2. **Add the restartGuard to every app** — copy the template above. Ten seconds of work saves thirty minutes of crash-loop diagnosis.
3. **On Windows, always launch Python services with `pythonw.exe`** — this applies beyond pm2. Any process manager (supervisord, NSSM, Windows Service wrappers) benefits from the same principle.



---

*The window you see isn't a bug — it's the operating system telling you, in the only language it speaks, that you launched the wrong type of binary.*
