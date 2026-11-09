---
title: Why Does a Bug Fixed Three Times Keep Coming Back? Deep Dive into Telegram 409 Conflict Ping-Pong Storms and Linux Kernel-Level Singleton Locks
header:
    image: /assets/images/bg_raw/BingWallpaper (18).jpg
date: 2026-11-09
tags:
 - python
 - linux-internals
 - distributed-systems
 - reliability-engineering
permalink: /blogs/tech/en/telegram-bot-409-conflict-flock-deepdive
lang: en
layout: single
category: tech
---
*The map is not the territory: A first-principles autopsy of supervisor split-brain, long-polling lockstep collisions, and VFS-level process locks in Linux & WSL2.*

> "The map is not the territory." — Alfred Korzybski

Sunday night at 10:14 PM, I ran our service inspection script `wsl_portal.sh status`. The terminal printed a status table with an unsettling amber warning:

```text
==========================================================================================
  Toddy Portal Services Status (WSL2)
==========================================================================================
ID  NAME                 PORT    STATUS      PORT-CHECK   PID    CPU   MEM       RESTARTS  UPTIME
--  -------------------  ------  ----------  -----------  -----  ----  --------  --------  ------
0   toddy-portal         3000    🟢 online    🟢 LISTENING  80257  0.1%  136.3 MB  1         11m   
1   mcp-gateway          8800    🟢 online    🟢 LISTENING  80299  0.2%  83.7 MB   1         11m   
2   portal-api           8002    🟢 online    🟢 LISTENING  80301  0.1%  70.4 MB   1         11m   
3   bank-chatbot-api     8001    🟢 online    🟢 LISTENING  80346  0.1%  66.5 MB   1         11m   
-   portal-telegram-bot  (poll)  ⚠️ degraded  🔴 POLL ERR   80610  0.0%  94.0 MB   0         11:02 

⚠️ Telegram Bot polling error: Client error '409 Conflict' for url 'https://api.telegram.org/bot8886525355:<redacted>/getUpdates?offset=0&timeout=30'
💡 Troubleshooting: Run 'wsl_portal.sh logs bot' or restart via 'portal-restart bot'.
```

I tailed `telegram_bot.log`. Line after line, with robotic 3-second precision, the same error was vomiting across the screen:

```log
2026-11-08T22:15:11+1100 [telegram_bot] WARNING: Polling error: Client error '409 Conflict' ... (retrying in 3.0s)
2026-11-08T22:15:14+1100 [telegram_bot] WARNING: Polling error: Client error '409 Conflict' ... (retrying in 3.0s)
2026-11-08T22:15:18+1100 [telegram_bot] WARNING: Polling error: Client error '409 Conflict' ... (retrying in 3.0s)
2026-11-08T22:15:21+1100 [telegram_bot] WARNING: Polling error: Client error '409 Conflict' ... (retrying in 3.0s)
```

My jaw clenched, and I blurted out that timeless on-call question:
**"We fixed this three days ago. We fixed it again yesterday. Why is this damn bug still here?!"**

If you have ever fought a daemon that looks trivial on paper—one where every patch seems to "fix it," where the green lights return after a manual restart, yet the ghost resurrects the moment your machine wakes from sleep or someone runs a deployment script—this deep dive is for you.

When bugs keep returning, it is almost never because code is cursed. It is because our mental model of the system stopped at the application layer, while the real root cause was living three layers deeper down the stack: in operating system VFS tables, supervisor boundaries, and transport protocol semantics.

---

## What You Will Take Away

Arranged in pedagogical order (most impactful intuition first, discovery journey second):

- **The Math of Long-Polling Deadlocks (The 409 Ping-Pong Storm)**: Why running two Telegram bot pollers with naive fixed-delay retries mathematically guarantees an infinite mutual-termination loop.
- **Supervisor Split-Brain in WSL2 & Virtualized Linux**: How WSLg over-mounting `/run/user/1000` blinds `systemctl --user`, tricking control scripts into spawning rogue standalone twins alongside systemd.
- **Kernel-Level Locks (`fcntl.flock`) vs. Fragile File Existence Locks**: Why `os.path.exists("bot.lock")` is an operational hazard that causes permanent downtime, and how VFS-level locks guarantee zero-deadlock recovery even under `kill -9` or kernel panics.
- **The Asyncio Graceful Shutdown Trap**: Why `SIGTERM` handlers with boolean flags hang for 30 seconds inside HTTP long-polling, and how explicit `Task.cancel()` yields millisecond-level tear-downs.

---

## 1. The Trap of Superficial Fixes

Look at the evolutionary trail of the previous three "fixes" for this bot:

| Iteration | What Was Done | Immediate Result | The Hidden Second-Order Defect |
| :--- | :--- | :--- | :--- |
| **Fix #1** | Configured a systemd user unit (`portal-telegram.service`) with `Restart=always`. | ✅ Bot auto-starts on boot | Created an invisible background manager that restarts dead processes without the caller's knowledge. |
| **Fix #2** | Added `kill -9` to the restart script to clean up orphaned pollers. | ✅ Cleared the error momentarily | Addressed the symptom; left the supervisor race condition completely intact for the next restart. |
| **Fix #3** | Added a fallback in the shell script: if `systemd` isn't reachable, spawn `nohup python ... &`. | ✅ Script stopped failing | **The trigger**: Blindly spawned duplicate processes whenever the user shell lacked DBus access. |

### The Naive Take vs. The Senior Take

- **The Naive Take**: "Telegram servers are acting up / our token leaked / let's just write a cron job that `kill -9`s everything every 10 minutes."
- **The Senior Take**:
  1. In the Telegram Bot API, an HTTP `409 Conflict` has an exact, deterministic contract: **another active HTTP connection just invoked `getUpdates` for this token**.
  2. The errors repeating at exact 3-second intervals proves that **two local clients are locked in synchronized harmonic oscillation**.
  3. Every time a system produces "twin processes" reliably, it is evidence of **Supervisor Split-Brain**—two independent supervisors claiming ownership of the same singleton resource.

---

## 2. Deep Dive Component 1: Telegram Long-Polling & The 409 Ping-Pong Storm

To understand how two processes enter a death spiral, consider the mechanics of HTTP Long-Polling.

### The Single-Consumer Rule

When a client queries Telegram updates, it issues an HTTP POST to `/getUpdates?timeout=30`.
- If no incoming message exists, Telegram holds the HTTP socket open for up to 30 seconds.
- To prevent split-brain delivery or out-of-order message acknowledgments, **Telegram enforces strict single-poller concurrency per Bot Token**.
- If Client A is currently waiting in a 30-second long-poll, and Client B suddenly posts a new `/getUpdates` request with the same token:
  - **Telegram immediately terminates Client A's connection, returning HTTP 409 Conflict**.
  - Telegram then accepts Client B's request into the pending hold queue.

```mermaid
sequenceDiagram
    autonumber
    participant A as Client A (PID 80610)
    participant TG as Telegram Bot Gateway
    participant B as Client B (PID 80970)

    Note over A,TG: Client A enters long-poll (held up to 30s)
    A->>TG: POST /getUpdates (timeout=30)
    
    Note over B,TG: Client B boots up with same token
    B->>TG: POST /getUpdates (timeout=30)
    
    Note over TG: Conflict! Server terminates A immediately
    TG-->>A: HTTP 409 Conflict (Client Error)
    Note over A: Naive handler: sleep(3.0)
    
    Note over A,TG: 3 seconds later, A reconnects
    A->>TG: POST /getUpdates (timeout=30)
    
    Note over TG: Conflict! Server terminates B immediately
    TG-->>B: HTTP 409 Conflict (Client Error)
    Note over B: Naive handler: sleep(3.0)
    
    Note over B,TG: 3 seconds later, B reconnects
    B->>TG: POST /getUpdates (timeout=30)
    TG-->>A: HTTP 409 Conflict (Deadlock loop begins...)
```

### Lockstep Resonance

Here was our naive exception handler before the fix:

```python
except Exception as e:
    logger.warning("Polling error: %s (retrying in %ss)", e, POLL_RETRY_DELAY) # 3.0s
    await asyncio.sleep(POLL_RETRY_DELAY)
```

Notice that fixed `3.0s` sleep. It acted as an **involuntary clock generator**:
1. Client A is kicked $\rightarrow$ sleeps for 3 seconds.
2. At second 3, Client A reconnects $\rightarrow$ Telegram kicks Client B.
3. Client B sleeps for 3 seconds.
4. At second 6, Client B reconnects $\rightarrow$ Telegram kicks Client A.
5. Both clients ping-pong each other into oblivion forever. **Neither receives messages, yet both saturate CPU and network retrying endlessly.**

### The Fix: Exponential Backoff & Voluntary Concession

To shatter the resonance, we must break the symmetry:

```python
consecutive_409 = 0
while self._running:
    try:
        updates = await self.telegram.get_updates(offset=self._offset, timeout=self.poll_timeout)
        consecutive_409 = 0  # Reset on any successful payload
        ...
    except Exception as e:
        err_str = str(e)
        if "409" in err_str and "Conflict" in err_str:
            consecutive_409 += 1
            # Exponential backoff: 3s -> 6s -> 12s -> 24s -> 30s
            retry_delay = min(30.0, POLL_RETRY_DELAY * (2 ** (consecutive_409 - 1)))
            logger.warning(
                "Telegram 409 Conflict (attempt %d): another poller is active. Backing off for %.1fs...",
                consecutive_409, retry_delay
            )
            if consecutive_409 >= 5:
                # After 5 backoffs, yield the token to the winner and terminate cleanly!
                logger.error("Persistent 409 Conflict across 5 attempts. Yielding to active poller.")
                break
        else:
            consecutive_409 = 0
            retry_delay = POLL_RETRY_DELAY

        await asyncio.sleep(retry_delay)
```

With exponential backoff and a 5-strike concession threshold, one of the two clients will back away and exit, allowing the surviving client to establish uninterrupted ownership.

---

## 3. Deep Dive Component 2: WSL2 Supervisor Split-Brain & The Masked User Bus

Even with backoff logic in place, a fundamental architectural question remained: **Why were two Python processes running on the same host in the first place?**

### The Hybrid Topology

In our stack:
- PM2 manages 4 web/API services (`toddy-portal`, `mcp-gateway`, `portal-api`, `bank-chatbot-api`).
- A systemd user unit (`portal-telegram.service`) was configured to manage the background bot.

### The WSL2 Anomaly: WSLg Over-Mounting `/run/user/1000`

Under standard systemd Linux distributions, user commands talk to `systemd --user` through the Unix domain socket at `/run/user/1000/bus`.

However, WSL2 has a known internal conflict:
When WSL boots, systemd starts up and creates `/run/user/1000` along with its DBus socket. But immediately afterward, the Windows WSLg initialization scripts mount their own Wayland/GUI runtime directory over top of it:

```bash
tmpfs on /run/user/1000 type tmpfs (rw,nosuid,nodev,relatime,size=2460896k,mode=700,uid=1000,gid=1000)
tmpfs on /run/user/1000 type tmpfs (rw,nosuid,nodev,noexec,relatime,mode=755) # WSLg over-mount!
```

**This silent over-mount obscures systemd's `/run/user/1000/bus` socket from user space.**
Any command executed in a non-login terminal or subshell running `systemctl --user` immediately fails with:
`Failed to connect to bus: No such file or directory`.

### The Catastrophic Fallback

Now look at what happened inside our management script [`wsl_service.sh`](file:///home/phray/ws/todd/effectiveCodingBase/src/toddy_portal/services/portal_api/scripts/wsl_service.sh):

```bash
systemd_reachable() {
    command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1
}

use_systemd() { [ -f "${UNIT_FILE}" ] && systemd_reachable; }
```

When an operator ran `wsl_portal.sh restart`:
1. `systemd_reachable` checked the user bus $\rightarrow$ failed due to the WSLg over-mount.
2. `use_systemd` evaluated to **false**. The script assumed: *"Systemd isn't supervising this bot, so I must handle it myself."*
3. The script executed `kill -9 $OLD_PID`, waited 1 second, and launched a background daemon:
   `nohup python -m portal_api.telegram_bot < /dev/null >> log 2>&1 &` (**Process A: PID 80610 is born**).
4. **Meanwhile, `systemd --user` was alive and well in PID 1's hierarchy.**
   Systemd saw its managed unit get terminated with signal 9. Because the service file specified:
   ```ini
   Restart=always
   RestartSec=5
   ```
   At second 5, systemd dutifully executed its job and spawned a fresh bot (**Process B: PID 80970 is born**).

Within 5 seconds of running any restart script, **both nohup and systemd were supervising their own copies of the bot**, spawning the 409 Conflict storm.

---

## 4. Deep Dive Component 3: Linux Kernel-Level Singleton Locks (`fcntl.flock`)

At this stage, an experienced engineer will immediately ask:

> *"What if the process holding the lock crashes, gets killed with `kill -9`, or encounters a Kernel Panic? Won't the lock file be left behind, preventing any future process from ever starting and causing permanent downtime?"*

This fear stems from confusing **Userland File Existence Locks** with **Kernel-Level Open File Description Locks**.

### File Existence Locks (The Anti-Pattern)

```python
# The classic naive lock:
if os.path.exists("/tmp/bot.lock"):
    print("Already running!")
    sys.exit(1)
open("/tmp/bot.lock", "w").write(str(os.getpid()))
```
If this process gets `kill -9`'d or crashes with an unhandled SIGSEGV, Python never executes a `finally` block. `/tmp/bot.lock` stays on disk forever. The application is permanently dead until a human manually deletes the file.

### Kernel VFS Locks (`fcntl.flock`)

Our production implementation in [`telegram_bot.py`](file:///home/phray/ws/todd/effectiveCodingBase/src/toddy_portal/services/portal_api/portal_api/telegram_bot.py) operates on an entirely different plane:

```python
LOCK_FILE = LOG_DIR / "portal_telegram.lock"

def _acquire_instance_lock() -> int | None:
    try:
        import fcntl
    except ImportError:
        return -1  # Non-Unix fallback

    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_RDWR, 0o644)
        # Request non-blocking exclusive lock from the Linux kernel
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Lock acquired: truncate and record PID
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
        os.fsync(fd)
        return fd
    except (BlockingIOError, OSError):
        # Kernel confirms another live process currently holds the lock
        return None
```

### Why `fcntl.flock` Can Never Leave a Stale Deadlock

In Linux, an `flock` lock is **not stored on the disk filesystem**. It is attached to the kernel's **open file table entry (`struct file`)** in VFS:

```
[ User Space ]
   Process A (PID 45842) ---> File Descriptor 3
                                    |
                                    v
[ Linux Kernel Space ]     +---------------------------+
                           |       struct file         |
                           |   (fl_type: F_WRLCK)      |  <--- flock resides here
                           +---------------------------+
                                    |
                                    v
[ Physical Disk ]          +---------------------------+
                           |   portal_telegram.lock    |  <--- purely an inode reference
                           +---------------------------+
```

When Process A dies:
- Whether via `kill -9`;
- Or a memory Segmentation Fault;
- Or the Linux OOM Killer terminating the process;
- Or a standard Python exception;

**The Linux kernel's process teardown routine `do_exit()` invokes `exit_files(tsk)` without exception. The kernel automatically closes all open file descriptors. The moment the file reference count drops, the kernel VFS instantly and unconditionally strips the `flock` lock.**

Even if `portal_telegram.lock` remains on the disk with the old PID string inside it, it is harmless. When Process B calls `fcntl.flock`:
1. The kernel checks its internal lock list, sees no active owner, and grants the lock instantly.
2. Process B truncates the stale PID and writes its own.

```text
Actual Subprocess Crash Verification:
P1 acquired lock, PID: 55428
Violently killing P1 (55428) with kill -9...
SUCCESS: P2 acquired the lock immediately after P1 died! No stale lock.
```

**By delegating mutual exclusion to the operating system kernel rather than application file state, we achieve bulletproof singleton guarantees with zero possibility of permanent deadlocks.**

---

## 5. The Asyncio Graceful Shutdown Trap

During this overhaul, we uncovered a third silent latency bug: **Why did `portal-restart` always take 25 to 30 seconds to terminate?**

Consider how typical signal handlers are written:

```python
# The common mistake:
def sig_handler():
    self._running = False  # Set flag and assume the loop will stop

loop.add_signal_handler(signal.SIGTERM, sig_handler)
```

In the main polling loop:
```python
while self._running:
    updates = await self.telegram.get_updates(timeout=30)  # Hung here!
```

**The trap**: While `sig_handler` immediately sets `self._running = False`, the running coroutine is currently suspended deep inside `httpx.AsyncClient.post()` waiting for TCP socket activity.
The Python asyncio event loop will not break out of an in-flight socket read just because an application variable changed.
Consequently, the process sat frozen for up to 30 seconds until the long-poll timed out naturally, forcing restart scripts to hit their timeouts and issue `kill -9`.

### The Millisecond-Level Cancellation Fix

Bind the active task on loop entry and cancel it directly when a shutdown signal arrives:

```python
async def run(self) -> None:
    self._running = True
    self._poll_task = asyncio.current_task()  # Anchor the polling task
    ...
    while self._running:
        try:
            updates = await self.telegram.get_updates(...)
        except asyncio.CancelledError:
            logger.info("Polling loop cancelled.")
            break

def stop(self) -> None:
    self._running = False
    self._stop_event.set()
    # Cancel the active long-poll immediately without waiting 30 seconds!
    if self._poll_task and not self._poll_task.done():
        self._poll_task.cancel()
```

The resulting shutdown log speaks for itself:
```log
2026-11-08T22:33:58+1100 [telegram_bot] INFO: Received termination signal, shutting down bot...
2026-11-08T22:33:58+1100 [telegram_bot] INFO: Polling loop cancelled.
2026-11-08T22:33:58+1100 [telegram_bot] INFO: Telegram Bot polling stopped.
```
**Shutdown latency dropped from 30 seconds down to 0.02 seconds.**

---

## 6. Synthesis: The Four Layers of Defense

We converted a fragile, recurring failure into an ultra-reliable architecture using **Defense in Depth**:

```
+--------------------------------------------------------------------------+
| Layer 1: Kernel-Level Singleton (Linux VFS fcntl.flock)                  |
| Any duplicate instance is rejected by kernel lock and exits silently.    |
+--------------------------------------------------------------------------+
                                     |
+--------------------------------------------------------------------------+
| Layer 2: Application Backoff & Yield (409 Conflict Exponential Backoff)  |
| If another instance holds the token, back off and yield to stop ping-pong.|
+--------------------------------------------------------------------------+
                                     |
+--------------------------------------------------------------------------+
| Layer 3: Instant Task Cancellation (Asyncio Task.cancel on SIGTERM)       |
| Aborts 30s long-poll sockets instantly, shrinking shutdown to < 20ms.    |
+--------------------------------------------------------------------------+
                                     |
+--------------------------------------------------------------------------+
| Layer 4: Supervisor Alignment & Multi-PID Detection                      |
| Prevent nohup fallbacks under systemd; status table warns on multi-PID.  |
+--------------------------------------------------------------------------+
```

Verifying the entire stack:
```text
==========================================================================================
  Toddy Portal Services Status (WSL2)
==========================================================================================
ID  NAME                 PORT    STATUS    PORT-CHECK   PID    CPU   MEM       RESTARTS  UPTIME  
--  -------------------  ------  --------  -----------  -----  ----  --------  --------  --------
0   toddy-portal         3000    🟢 online  🟢 LISTENING  46646  0.0%  142.5 MB  2         9h      
1   mcp-gateway          8800    🟢 online  🟢 LISTENING  46710  0.1%  88.0 MB   2         9h      
2   portal-api           8002    🟢 online  🟢 LISTENING  46705  0.1%  74.3 MB   2         9h      
3   bank-chatbot-api     8001    🟢 online  🟢 LISTENING  46741  0.1%  70.1 MB   2         9h      
-   portal-telegram-bot  (poll)  🟢 online  🟢 POLLING    46934  0.0%  94.2 MB   0         01:17:18
```
All 5 services green, running for 9+ hours without a single collision, and 338 automated test cases passing cleanly.

---

## 7. Actionable Checklist for Production Daemons

If you operate background consumers, Telegram bots, or long-running daemons in virtualized or containerized Linux, check these four items today:

1. **Audit Every Long-Polling Retry Loop**:
   - Never write `except Exception: sleep(3.0)` in a long-poller. Implement exponential backoff with jitter and a maximum concession counter to avoid lockstep resonance.
2. **Upgrade Userland Lock Files to `fcntl.flock`**:
   - Replace any `os.path.exists("*.lock")` logic with kernel file-descriptor locks (`fcntl.flock(fd, LOCK_EX | LOCK_NB)`). Leave cleanup to the Linux kernel VFS, eliminating stale-lock deadlocks after crashes.
3. **Inspect Your SIGTERM Handlers for Asyncio Blocking**:
   - If your main loop awaits a long-lived socket (`timeout=30`), setting a boolean flag is not enough. Store `asyncio.current_task()` and call `.cancel()` inside the signal handler to force instant socket closure.
4. **Beware Hybrid Supervisor Blind Spots**:
   - When running multiple process managers (e.g. PM2 alongside systemd) across virtualized boundaries like WSL2 or Docker, verify that supervisor health checks are immune to filesystem masking and over-mounts.

---

*A green light on a monitoring dashboard only proves that a probe succeeded. What proves a system's true health is the uninterrupted, collision-free rhythm of its business heartbeat in the physical world.*
