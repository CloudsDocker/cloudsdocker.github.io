---
title: "Build a Bulletproof System: Lessons from 1,966 Crash Restarts"
header:
    image: /assets/images/hd_nodejs_faq.png
date: 2026-11-04
tags:
 - devops
 - debugging
 - reliability
 - observability
permalink: /blogs/tech/en/pm2-max-restarts-is-not-a-budget
lang: en
layout: single
category: tech
---

> Changing the temperature is hard. Changing the thermometer is easy. Changing your weight is hard — changing the scale is trivial.

# `max_restarts: 5` Did Not Stop 1,966 Restarts

*The gap between "the process is alive" and "the service works" is wide enough to hide ten hours in*

The page wouldn't load from my laptop. I tried the other IP. Still nothing.

My first theory was the one you'd have reached for too: Tailscale is being Tailscale again.

Then I SSH'd into the WSL box and ran `pm2 list`:

```
│ id │ name         │ status │ restarts │
│ 0  │ toddy-portal │ online │ 1966     │
```

`online`.

Meanwhile `ss -tlnp | grep :3000` returned nothing at all. The port was dead.

**1,966 restarts** — against a config that says, in plain text, `max_restarts: 5`.

This isn't a "and then I fixed the bug" post. It's about the twenty minutes it took me to notice that for ten straight hours the service had been killing itself every fifteen seconds while all three of my instruments — PM2's status, PM2's restart ceiling, and the smoke test I wrote myself — reported green.

## What you'll walk away with

- **A testable intuition**: `max_restarts` does not mean "give up after N restarts." It means "arm the crash detector for `min_uptime × max_restarts` milliseconds." It's a time window, not a counter budget.
- **A counter-intuitive result**: the exponential backoff you configured (`exp_backoff_restart_delay`) actively *spends* that window. The politer your backoff, the more reliably your crash protection never fires.
- **A ruler** for telling the difference between a health check that measures your weight and one that measures the scale.

I've ordered this most-useful-first, not in the order I discovered it — my actual order wasted twenty minutes on the network.

---

## 1. Line up the three instruments that lied

The right first question in an outage isn't "what's broken." It's "which of my signals can I trust?"

| Instrument | What it said | The truth | Why it wasn't lying |
|---|---|---|---|
| `pm2 list` → `online` | The process is alive | It had just been forked and would die 0.15s later | PM2 reports **process** state. It never claimed to report service state |
| `restarts: 1966` with `max_restarts: 5` | The ceiling failed | The ceiling doesn't mean what the name says | See §3 — that's the main course |
| `wsl_portal.sh test` → all green | Service healthy | It only curls `127.0.0.1`, and my failure was **remote** | The thing it tested really was fine. It just wasn't my problem |

Three instruments, zero lies, and I was thoroughly misled for ten hours.

> A signal's value isn't its accuracy. It's the distance between what it measures and the question you're asking.

### Five whys

```
Portal won't load from the laptop
  └─ why? nothing is listening on port 3000
      └─ why? the Next.js process exits 0.15s after launch
          └─ why? app.prepare() rejects: no production build found
              └─ why? .next/ exists but contains no BUILD_ID
                  └─ why? that directory is leftover debris from a turbopack dev run
```

The root cause is five levels down. The top level pointed at the network.

---

## 2. A `.next/` directory is not a build

This line repeated 1,966 times in the PM2 error log:

```text
[DEBUG] after next(), before prepare()
[DEBUG] prepare() REJECTED: Error: Could not find a production build in
        the '.next' directory. Try building your app with 'next build'
        before starting the production server.
```

And yet `.next/` was right there:

```bash
$ ls .next/
cache/  diagnostics/  server/  static/  types/  lock  package.json  turbopack
$ cat .next/BUILD_ID
cat: .next/BUILD_ID: No such file or directory
```

This is the first false positive of the story and the one most likely to bite you again: **Next.js dev mode and production mode share the directory name `.next/` while writing two completely different things into it.**

| | dev (turbopack) | production (`next build`) |
|---|---|---|
| writes `cache/` `server/` `static/` | ✅ | ✅ |
| writes `BUILD_ID` | ❌ | ✅ |
| `next start` accepts it | ❌ | ✅ |

Which makes any check shaped like `if [ -d .next ]` **structurally wrong**. The file `next start` actually opens is `BUILD_ID`, so that's the file your check has to open:

```bash
[ -f "${PORTAL_DIR}/.next/BUILD_ID" ]
```

> **Worth stealing for an interview answer**: when you need to check "is this artifact ready," don't pick a path that looks related. Read the consumer's source and find the exact file it opens. A directory is a convention; a file is a contract.

---

## 3. `max_restarts` is not a restart budget

This is the chapter I actually wanted to write, because it made me re-humble about a config key I was sure I understood.

Here's the block from my `ecosystem.wsl.config.js`. When I wrote it, I thought I was doing defensive design:

```js
const restartGuard = {
  autorestart: true,
  min_uptime: "10s",
  max_restarts: 5,
  exp_backoff_restart_delay: 2000,
};
```

My mental model: *if an app crashes 5 times, PM2 gives up instead of thrashing the machine.*

**That model is wrong.** From PM2's own source (`lib/God.js`, v6):

```js
var min_uptime   = typeof(proc.pm2_env.min_uptime)   !== 'undefined' ? proc.pm2_env.min_uptime   : 1000;
var max_restarts = typeof(proc.pm2_env.max_restarts) !== 'undefined' ? proc.pm2_env.max_restarts : 16;

if ((Date.now() - proc.pm2_env.created_at) < (min_uptime * max_restarts)) {   // ← outer: time window
  if ((Date.now() - proc.pm2_env.pm_uptime) < min_uptime) {                   // ← inner: this life was short
    proc.pm2_env.unstable_restarts += 1;
  }
}

if (proc.pm2_env.unstable_restarts >= max_restarts) {
  proc.pm2_env.status = cst.ERRORED_STATUS;   // only here does PM2 actually give up
  overlimit = true;
}
```

Stare at that outer `if` for three seconds:

```js
(Date.now() - created_at) < (min_uptime * max_restarts)
```

`max_restarts` isn't used as a count there. **It's used as a multiplier.** Multiplied by `min_uptime`, it produces a span of wall-clock time. With my config:

```
10,000 ms × 5 = 50,000 ms = 50 seconds
```

**PM2 only counts unstable restarts during the app's first 50 seconds of life.** Past that, the outer `if` is false forever, `unstable_restarts` never increments again, and `>= max_restarts` can never become true. The crash protection has been **permanently and silently disarmed**.

### The part that's genuinely backwards: backoff eats the window

Now fold in `exp_backoff_restart_delay: 2000`. Same file:

```js
proc.pm2_env.prev_restart_delay = Math.floor(Math.min(15000, proc.pm2_env.prev_restart_delay * 1.5))
```

Each restart waits 1.5× longer, capped at 15s. So during that precious 50-second detection window, PM2 spends most of its time **asleep**:

| Crash # | Elapsed | Backoff wait | Window left |
|---|---|---|---|
| #1 | 0.15 s | 2.0 s | 49.8 s |
| #2 | 2.3 s | 3.0 s | 47.7 s |
| #3 | 5.5 s | 4.5 s | 44.5 s |
| #4 | 10.1 s | 6.75 s | 39.9 s |
| #5 | 17.0 s | 10.1 s | 33.0 s |
| #6 | 27.3 s | 15.0 s (capped) | 22.7 s |

The two conditions are **AND**-ed. If either fails, the counter stays frozen:

- **Outer**: must be within the first 50 seconds. Backoff dilutes the crash events, so running out the window before hitting 5 is easy.
- **Inner**: this particular life must be shorter than 10 seconds. True on an idle box — I measured the crash at **0.153 s** — but that night the WSL VM was carrying a full Airflow container stack and 60 MCP processes, at 95% memory, 10GB into swap, with IO pressure at `full avg10=14%`. And `server.js` opens a SQLite file across the 9P mount at `/mnt/c/Users/.../toddy_backup.db` on startup. Under that load, a single boot taking more than 10 seconds is entirely ordinary.

I don't have per-attempt timings from that night, so **I can't say which condition failed first.** That's exactly the point worth making: **both conditions are temporal, both fail without telling you, and the failure looks identical either way — a guard labelled "max 5" delivering 1,966.**

> This is the clean form of a leaky abstraction: `max_restarts` promises counting semantics and implements timing semantics. The gap between the name and the mechanism is where every "I thought that would catch it" outage lives.

### Check the arithmetic

```
1,966 restarts × 15 s (backoff cap) ≈ 8.19 hours
```

Add node's cold-start cost per attempt and you've filled the ten hours between 22:56 last night and 09:10 this morning. The numbers close the loop.

---

## 4. `created_at` survives a reboot

One more part, or §3 can't explain why the counter was stuck from the very first crash.

PM2 sets `created_at` in `God.executeApp()` like this:

```js
if (!env_copy.created_at)
  env_copy['created_at'] = Date.now();
```

**Only when it's empty.** And the post-crash auto-restart path goes straight through `God.executeApp(proc.pm2_env)` — `created_at` is carried over untouched. Only an explicit `pm2 restart` runs `God.resetState()`:

```js
God.resetState = function(pm2_env) {
  pm2_env.created_at = Date.now();
  pm2_env.unstable_restarts = 0;
  pm2_env.prev_restart_delay = 0;
};
```

Worse: `pm2 save` writes `created_at` verbatim into `~/.pm2/dump.pm2`:

```
dump.pm2 written at   2026-11-03 22:56:34
  created_at          2026-11-03 22:56:31
  unstable_restarts   1
```

So after `pm2 resurrect`, the app's *age* is inherited from its previous life. If that `created_at` is already hours old, the 50-second detection window has **already expired** by the time the app comes back. The crash protection is dead on arrival.

| Path | `created_at` | Crash detector |
|---|---|---|
| Manual `pm2 restart` | refreshed | re-armed for 50s |
| Auto-restart after a crash | inherited | keeps counting down |
| `pm2 resurrect` (boot, or after `wsl --shutdown`) | **inherited from the dump** | **can be expired on arrival** |

If you use `pm2 save` + `pm2 startup` for boot persistence, that last row is a real trap: **you assume rebooting the machine resets state, but PM2 checkpointed time along with everything else.**

---

## 5. A smoke test against `127.0.0.1` tests nothing

My script's `test` subcommand was three for three:

```bash
curl -s -f -m 3 http://127.0.0.1:3000
curl -s -f -m 3 http://127.0.0.1:8002/healthz
curl -s -m 3 http://127.0.0.1:8800/health
```

But my failure was "won't load **from the laptop**." Loopback carries exactly zero information about that: it doesn't exercise the interface binding (`127.0.0.1` vs `0.0.0.0`), the Tailscale overlay, or the firewall.

I also managed to step on Tailscale twice, both times by **treating two nodes as one**:

```
100.85.1.56     aidra-studio-wsl     linux     ← the portal runs here
100.124.38.9    aidra-studio         windows   ← different machine, nothing on 3000
100.104.0.40    todd-macbook-pro     macOS     offline, last seen 107d ago
```

The WSL guest and its Windows host are **two separate tailnet nodes with two separate IPs**. The second URL I tried pointed at the Windows node, where nothing was ever going to answer.

And that last row is more final than any of it: my laptop hadn't been on the tailnet in **107 days**. Even a perfectly healthy service was unreachable from it.

> In distributed debugging, the most expensive hours go to discovering that two things were, in fact, two things.

---

## 6. Turn tribal knowledge into an artifact

The fix itself is `npm run build`. Not interesting.

What's interesting is that **every insight above, left in my head, would have re-run this outage in three months.** So the real deliverable is encoding them in the script:

```bash
check_build() {
    # A '.next' directory can exist from a dev/turbopack run with no production
    # build in it. BUILD_ID is the file 'next start' actually looks for, so that
    # is what we check -- otherwise PM2 silently crash-loops on prepare().
    if [ ! -f "${PORTAL_DIR}/.next/BUILD_ID" ]; then
        echo "❌ No production build found (${PORTAL_DIR}/.next/BUILD_ID missing)."
        echo "   Run 'npm run build' in ${PORTAL_DIR} first."
        exit 1
    fi
}
```

Plus the smoke-test check that actually corresponds to the failure mode:

```bash
# 4. Tailscale — loopback working tells us nothing about remote access
TS_IP=$(tailscale ip -4 2>/dev/null | head -1)
if [ -z "${TS_IP}" ]; then
    echo "4. Tailscale UI reachability... ⏭️  SKIPPED (no tailscale0 in this WSL)"
else
    echo -n "4. Testing Toddy Portal UI over Tailscale (http://${TS_IP}:3000)... "
    if curl -s -f -o /dev/null -m 5 "http://${TS_IP}:3000"; then
        echo "✅ OK"
    else
        echo "❌ FAILED (port 3000 may be bound to 127.0.0.1 only)"
    fi
fi
```

Then I moved `BUILD_ID` aside to verify the guard in the failing direction. It held, exited 1, and — importantly — stopped the run **before** PM2 was ever invoked:

```
$ ./scripts/wsl_portal.sh restart
❌ No production build found (/home/phray/.../.next/BUILD_ID missing).
   Run 'npm run build' in /home/phray/... first.
exit=1
```

And then green — green that now means something:

```
1. Testing Toddy Portal UI (http://127.0.0.1:3000)... ✅ OK
2. Testing portal-api Health (http://127.0.0.1:8002/healthz)... ✅ OK
3. Testing mcp-gateway Health (http://127.0.0.1:8800/health)... ✅ OK
4. Testing Toddy Portal UI over Tailscale (http://100.85.1.56:3000)... ✅ OK
```

> A senior engineer fixes this bug. A principal engineer makes the bug announce itself in three seconds next time. The difference isn't who reads PM2's source — it's who bothers to move what they just learned out of their head and into the repo.

---

## Stitching it together

Three independent components misled me, and all three made **the same mistake**:

| Instrument | What it measures (the scale) | What it should measure (your weight) |
|---|---|---|
| `pm2 list` → `online` | a process got forked | the port is listening and returns 200 |
| `max_restarts: 5` | crash density in the first 50s | whether this app can start at all |
| `wsl_portal.sh test` | loopback is reachable | the path I actually use is reachable |
| `ls .next/` | the directory exists | `BUILD_ID` exists |

Everything in the left column is **cheap, easy to measure, easy to implement** — which is precisely why it's the default. The right column is expensive, so tools don't hand it to you.

**So here's my position: treat any health check you have never personally watched turn red as green noise.** A check that has never failed carries the same information as a hardcoded `echo "✅ OK"`.

---

## Do this today

1. Open your own `ecosystem.config.js` and multiply `min_uptime × max_restarts`. That number of seconds is the **entire lifetime** of your crash protection. If you also set `exp_backoff_restart_delay`, ask the follow-up: how much of that window does the backoff sleep through?
2. Run `pm2 jlist | jq '.[] | {name, restart_time, unstable_restarts}'`. Any app with a three-digit `restart_time` and `unstable_restarts: 0` deserves a look at its logs — that combination is the signature of disarmed protection.
3. Add a precondition to every `*_service.sh start` that checks **the file the consumer actually opens** (`BUILD_ID`, the `.jar`, `dist/index.js`) — not the directory it lives in.
4. Grep your smoke tests for `127.0.0.1`. If your users come from another machine, those lines cover 0% of real failures. Add at least one that traverses the real path.
5. Run the check backwards once: deliberately remove the artifact and confirm your guard goes red. A guard that has never gone red isn't a guard.

---

*Monitoring isn't about knowing the system is alive. It's about knowing when to stop believing the instruments.*
