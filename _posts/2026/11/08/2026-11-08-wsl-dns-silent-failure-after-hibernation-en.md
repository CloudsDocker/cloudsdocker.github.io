---
title: 'It Pings, the PID Is Alive — but Your Service Is Already Dead: WSL2 DNS Failure After Hibernation'
header:
    image: /assets/images/jpa_camel_snake.png
date: 2026-11-08
tags:
 - wsl
 - networking
 - dns
 - debugging
 - reliability
permalink: /blogs/tech/en/wsl-dns-silent-failure-after-hibernation
lang: en
layout: single
category: tech
---
*From "false aliveness" to "transparent self-healing" — a deep post-mortem of a virtualized-network fault.*

On a Sunday at 11:42 in the morning, I sent my own chat bot this message:

`/quote The best resting place for an idea is never to be enshrined, but to keep growing.`

No reply. I sent it twice. The other end stayed dead silent.

My first instinct was to check the service status. I typed `wsl_portal.sh status`, and the console printed a table that looked perfectly healthy:

```
==========================================================================================
  awesome Portal Services Status (WSL2)
==========================================================================================
ID  NAME                 PORT    STATUS    PORT-CHECK   PID    CPU   MEM      RESTARTS  UPTIME  
--  -------------------  ------  --------  -----------  -----  ----  -------  --------  --------
0   awesome-portal       3000    🟢 online  🟢 LISTENING  14577  0.1%  64.1 MB  16        14h 41m 
1   portal-api           8002    🟢 online  🟢 LISTENING  14628  0.0%  15.0 MB  15        14h 41m 
2   hr-chatbot-api       8001    🟢 online  🟢 LISTENING  14633  0.0%  14.4 MB  14        14h 41m 
3   mcp-gateway          8800    🟢 online  🟢 LISTENING  14716  0.2%  45.7 MB  17        14h 41m 
-   portal-the-chat-bot  (poll)  🟢 online    N/A (bot)  15375  0.0%  32.7 MB  0         14:40:52
```

Every indicator was green. `portal-the-chat-bot` sat there showing `🟢 online`, PID `15375`, an uptime of a full 14 hours 40 minutes.

But when I switched to the log file `the-chat-bot.log`, the picture was the exact opposite — the screen was drowned in the same error line, scrolling for over four hours straight:

```log
2026-11-08T07:34:00+1100 [the-chat-bot] WARNING: Polling error: [Errno -3] Temporary failure in name resolution (retrying in 3.0s)
2026-11-08T07:34:13+1100 [the-chat-bot] WARNING: Polling error: [Errno -3] Temporary failure in name resolution (retrying in 3.0s)
...
2026-11-08T11:42:06+1100 [the-chat-bot] WARNING: Polling error: [Errno -3] Temporary failure in name resolution (retrying in 3.0s)
```

From the moment the laptop woke at 7:34 that morning, every 13 seconds it hit a DNS failure. It never crashed, never tripped the system's `Restart=always`, just kept retrying inside a dead loop.

**The process was alive, the port wasn't conflicting, monitoring was all green — but it had been deaf and mute for four hours.**

## What you'll walk away with

Sorted most-useful-first, not in the roundabout order I actually hit them — the detours I took, you get to step straight over.

- **A first-principles instinct for seeing through a "monitoring illusion"**: why is `kill -0 $PID` the laziest and most dangerous health check there is? `kill -0 $PID` only checks whether a process *exists*, never whether it's doing useful work. A process can exist and still be wedged in an unresponsive state. Anchor health on the core feedback loop — HTTP request, DB query latency, API round-trip — not on the presence of a PID.
- **An X-ray of WSL2's cross-boundary networking**: why, after the host hibernates, does NAT routing survive intact while UDP 53 alone gets severed into a black hole?
- **A zero-external-dependency, application-level self-healing fix in pure Python**: transparent DNS fallback with nothing but the standard library — without waiting out the glibc timeout, without depending on the host's DNS — plus the hidden trap where `anyio` hands you `bytes`, not `str`.
- **Two "I thought I fixed it but didn't" classics**: why editing `wsl.conf` without a restart equals changing nothing, and why `systemd=true` quietly undoes your DNS fix.

## 1. The scariest crash isn't a crash — it's a fake death

In software reliability engineering, a dead process is never the scary one. A crash produces a core dump, trips systemd or supervisor into restarting it, and sets off the alarm immediately.

The scary one is the **zombie service**: its heartbeat is still there (the PID is alive), it holds memory, the OS keeps scheduling it — but its effective throughput has dropped to zero.

Put the two observation sources side by side:

| Observation axis | Signal on the surface | The truth behind it | Verdict |
| --- | --- | --- | --- |
| **OS process table** (`ps`) | PID `15375` alive 14h 40m | Process spinning a `sleep(3.0)` dead loop | Misread as healthy |
| **Status tool** (`status_table.py`) | `🟢 online` | Only ran `kill -0 15375` | False positive |
| **Real business** (`get_updates`) | 4 hours of no response | `api.telegram.org` fails to resolve | **Business is dead** |

This is a textbook **symmetry breaking**: the symmetry between "the process exists" and "the service works" has been broken.

When we reduce a health check to a single system call, `kill -0`, what we actually measure is "the OS still remembers this PID" — not "this process is still working for a human."

> **First principle**: never monitor a process's breathing, monitor its throughput. If a polling service fails its handshake N times in a row, semantically it is already dead.

## 2. Prying open the virtual-network black box: why did hibernation lose only DNS?

To get to the truth, I ran a classic layered probe inside WSL, peeling from the bottom of the network up to the application.

### Step 1: test L3 routing and external reachability
```bash
$ ping -c 1 8.8.8.8
64 bytes from 8.8.8.8: icmp_seq=1 ttl=109 time=13.2 ms
```
**Result**: ICMP is fine, 13ms straight to an external IP. The underlying virtual NAT switch is working.

### Step 2: test L4/L7 by connecting straight to Telegram's servers
If names won't resolve, what about bypassing DNS and opening a TLS connection directly to Telegram's public IP?
```bash
$ curl -I --resolve api.telegram.org:443:149.154.166.110 https://api.telegram.org
HTTP/2 302 
server: nginx/1.30.1
location: https://core.telegram.org/bots
```
**Result**: instant response (sub-100ms), certificate validated cleanly. This proves:
1. TCP/HTTPS from the host to the outside world is unobstructed;
2. TLS SNI certificate negotiation is flawless;
3. **the single break point is 100% stuck at name resolution (DNS).**

### Step 3: compare the system default DNS against a public DNS

First look at the system's `/etc/resolv.conf`:
```
nameserver 10.0.0.1
```
This is the virtual gateway address WSL2 auto-generates at boot, pointing at the Windows host's Hyper-V virtual switch.

Query the two resolvers in turn:
```bash
# 1. the host's virtual proxy:
$ dig @10.0.0.1 google.com +time=2 +tries=1
;; communications error to 10.0.0.1#53: timed out

# 2. a public DNS:
$ dig @8.8.8.8 google.com +time=2 +tries=1
;; Query time: 8 msec
;; SERVER: 8.8.8.8#53(8.8.8.8) (UDP)
google.com.  IN  A  172.217.25.174
```

The truth is out: **`10.0.0.1:53` is completely gone, while `8.8.8.8:53` answers in 8 milliseconds.**

After the host hibernates and wakes, the Hyper-V virtual switch's DNS proxy on `10.0.0.1:53` dies, but the L3 NAT path it set up survives — so ICMP and direct-IP TCP keep working, and only UDP 53 to the virtual gateway falls into a black hole.

## 3. Don't hang your app's life on /etc/resolv.conf

A lot of people stop their fix right here: edit `/etc/wsl.conf`, disable `generateResolvConf`, then hard-code `/etc/resolv.conf` to `8.8.8.8`. That looks like a direct fix, but as a systems architect you have to push further:

> **If a service runs in a sandbox, a container, or an ops-managed box where you can't freely edit system config, and the host's DNS dies — does your app just have to die with it?**

The answer is: **build an autonomous escape hatch at the application layer.**

### A transparent DNS self-healing layer in pure Python

We designed and injected a zero-external-dependency resilient DNS interceptor: [`dns_resilience.py`](file:///home/you/ws/main/repo/src/one-llm-based-app/services/portal_api/dns_resilience.py).

Its logic is deliberately restrained and precise:

1. **Protocol-level fallback**: use the standard library `socket` to build a raw UDP DNS query packet and send it straight to `8.8.8.8` and `1.1.1.1`;
2. **In-memory parsing**: hand-write 15 lines of binary `unpack` logic to parse the A records and CNAME chain in the DNS Answer section;
3. **Static backstop mapping**: hard-code the core services (e.g. `api.telegram.org` -> `149.154.166.110`) as an absolute last line of defense;
4. **Transparent hook**: wrap `socket.getaddrinfo` at runtime, completely invisible to the business code.

The core interception mechanism:

```python
def resilient_getaddrinfo(host: Any, port: Any, family: int = 0, type: int = 0, proto: int = 0, flags: int = 0) -> Any:
    global _system_dns_failing_until
    now = time.time()

    # Normalize the hostname (handle both bytes and str)
    if isinstance(host, bytes):
        host_str = host.decode("ascii", errors="ignore").strip().rstrip(".")
    elif isinstance(host, str):
        host_str = host.strip().rstrip(".")
    else:
        host_str = str(host or "").strip()

    is_named_host = (
        bool(host_str)
        and not host_str.replace(".", "").isdigit()
        and host_str not in ("localhost", "127.0.0.1", "::1")
    )

    # 1. Fast circuit-break: if system DNS just failed, go straight to fallback,
    #    never let glibc drag us through its 10s timeout
    if is_named_host and now < _system_dns_failing_until:
        ips = resolve_fallback(host_str)
        if ips:
            try:
                return _orig_getaddrinfo(ips[0], port, family, type, proto, flags)
            except Exception:
                pass

    # 2. Normal path: trust the system DNS first
    try:
        res = _orig_getaddrinfo(host, port, family, type, proto, flags)
        _system_dns_failing_until = 0.0  # system DNS recovered, clear the failure flag
        return res
    except socket.gaierror as exc:
        if is_named_host:
            logger.warning("System DNS failed for %s (%s). Engaging fallback DNS...", host_str, exc)
            _system_dns_failing_until = now + 60.0  # open a 60s fast fallback window
            ips = resolve_fallback(host_str)
            if ips:
                return _orig_getaddrinfo(ips[0], port, family, type, proto, flags)
        raise exc
```

### A deeply buried trap: `anyio` doesn't pass `str`

While building this self-healing module I hit a genuinely instructive detail.

In unit tests with `requests` or `urllib`, everything looked perfect. But the moment the code moved into the `httpx.AsyncClient`-based chat bot, it still threw `ConnectTimeout`. After stepping through `httpcore` and `anyio` source, I found the undercurrent.

The modern async library `anyio` runs this before calling `getaddrinfo`:

```python
encoded_host = idna2008_resolve(host) if isinstance(host, str) else host
```

To support internationalized domain names, it encodes the host into **`bytes`** (i.e. `b'api.telegram.org'`) at the bottom layer. If your interceptor only checks whether `host` is a `str`, then every request from a modern async HTTP stack (`httpx`, `fastapi`, `httpcore`) sails straight past your interception and back into the 10-second system-DNS timeout.

```python
if isinstance(host, str):  # ❌ always False for anyio!
```

A robust low-level network tool must **defensively accept both `bytes` and `str`.**

## 4. Erase the lie from the status panel

With self-healing solved, we still had to kill the fatal "false-positive monitor." The old `status_table.py` logic was blunt — it only checked whether the process was alive:

```python
# old code: as long as the PID is alive, stamp it 🟢 online
tg_status = "🟢 online" if tg_running else "🔴 stopped"
```

We rebuilt it into a probe that senses the real business pulse by inspecting the actual polling heartbeat in the logs:

```python
# new code: inspect the real polling heartbeat in the logs
if tg_running:
    # pull the last 4KB of logs
    recent_errs = [l for l in lines[-10:] if "Polling error:" in l]
    if recent_errs:
        last_err = recent_errs[-1]
        if "Temporary failure in name resolution" in last_err:
            tg_status = "⚠️ degraded"
            tg_port_check = "🔴 NO DNS"
            tg_warning_note = "⚠️ Chat bot cannot resolve api.telegram.org (WSL DNS failure)."
    else:
        tg_port_check = "🟢 POLLING"
```

Now, when DNS fails, the console stops papering over it and honestly flashes red:
```
-   portal-the-chat-bot  (poll)  ⚠️ degraded  🔴 NO DNS     15375  0.0%  44.1 MB  0  14:52:51
⚠️ Chat bot cannot resolve api.telegram.org (WSL DNS failure).
💡 Troubleshooting: Run 'wsl_portal.sh logs bot' or restart via 'portal-restart bot'.
```

And once self-healing kicks in, the status reads clearly:
```
-   portal-the-chat-bot  (poll)  🟢 online    🟢 POLLING    70022  0.0%  93.7 MB  0  03:01
```

## 5. "Edit wsl.conf and you're done"? — two traps that undo your fix

If you rush off to edit config based only on the analysis above, you'll likely fall into the two pits I did. They interlock; you have to understand both to fix it in one pass.

### Trap 1: editing wsl.conf without restarting WSL — equals changing nothing

In my first round I added to `/etc/wsl.conf`:

```ini
[network]
generateResolvConf = false
```

Then I deleted the `/etc/resolv.conf` symlink and hand-wrote a static file pinned to public DNS:

```
nameserver 8.8.8.8
nameserver 1.1.1.1
nameserver 10.0.0.1
```

Looked perfect. But a few minutes later, `cat /etc/resolv.conf` showed it overwritten back:

```
# This file was automatically generated by WSL. To stop automatic generation of this file...
nameserver 10.0.0.1
```

**Why**: `wsl.conf` is read when the WSL instance **boots**. The currently running instance is still on the old config — `generateResolvConf` is effectively still `true`, and WSL's internal daemon keeps maintaining `/etc/resolv.conf`. You change it by hand, it changes it back.

**Fix**: after editing `wsl.conf`, run a full shutdown from the **Windows side**:

```powershell
wsl --shutdown
```

Wait 3–5 seconds and restart. Only then does `generateResolvConf = false` truly take effect.

### Trap 2: the `systemd=true` takeover — you handed it to systemd-resolved, not to yourself

When I also enabled `systemd=true` in `wsl.conf` (standard on modern WSL2 distros), a second surprise appeared.

After `wsl --shutdown` and a restart, I checked `/etc/resolv.conf`:

```bash
$ ls -la /etc/resolv.conf
lrwxrwxrwx 1 root root 39 Nov  8 21:18 /etc/resolv.conf -> ../run/systemd/resolve/stub-resolv.conf

$ cat /etc/resolv.conf
nameserver 127.0.0.53
options edns0 trust-ad
```

The file had become a **brand-new symlink** — no longer to WSL's `/mnt/wsl/resolv.conf`, but to `systemd-resolved`'s stub config. The nameserver was now `127.0.0.53`, systemd-resolved's local stub resolver.

What happened? Once `generateResolvConf = false` took effect, WSL stopped managing `/etc/resolv.conf`. But with `systemd=true`, systemd's init starts `systemd-resolved`, which has its own DNS management and relinks `/etc/resolv.conf` to its own stub.

Check resolved's upstream config:

```bash
$ resolvectl status
Global
         Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
  resolv.conf mode: stub

Link 2 (eth0)
    Current Scopes: none
         Protocols: -DefaultRoute ...
```

**No upstream DNS server configured at all.** systemd-resolved started, took over every DNS query, but has nowhere to forward them — so everything sent to `127.0.0.53` falls into a black hole.

A perfect failure chain:

```
your hand-written resolv.conf (8.8.8.8)
    ↓ wsl.conf not restarted, WSL overwrites it back to 10.0.0.1
    ↓ wsl --shutdown then restart
    ↓ WSL stops generating resolv.conf (generateResolvConf=false now active)
    ↓ but systemd-resolved takes over, creates a new symlink → 127.0.0.53
    ↓ resolved has no upstream DNS → every query times out
    ↓ DNS is still broken, it just died a different way
```

**Fix**: don't fight systemd-resolved — configure it. Add a drop-in telling it to use public DNS upstream:

```bash
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo tee /etc/systemd/resolved.conf.d/public-dns.conf << 'EOF'
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=8.8.4.4 1.0.0.1
EOF

sudo systemctl restart systemd-resolved
```

Verify:

```bash
$ resolvectl status | head -6
Global
           Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
    resolv.conf mode: stub
         DNS Servers: 8.8.8.8 1.1.1.1
Fallback DNS Servers: 8.8.4.4 1.0.0.1

$ dig google.com +short
172.217.25.174  ✅
```

This drop-in is auto-loaded by systemd-resolved on every WSL boot — it won't get overwritten, and you don't have to reconfigure it each time.

## 6. The three-layer defense, summarized

Building a highly reliable system isn't about "never failing" — it's about shrinking the blast radius of a failure through layered defenses.

| Defense layer | Where it lives | What it solves | Key mechanism |
|---|---|---|---|
| **Layer 1: system base** | `/etc/wsl.conf` + `resolved.conf.d/` | Cut WSL's single dependency on the Windows virtual proxy | `generateResolvConf = false` + systemd-resolved upstream config |
| **Layer 2: app self-healing** | `dns_resilience.py` | Even if the base collapses, critical services escape | Intercept `getaddrinfo` + raw UDP query + 60s fast circuit-break |
| **Layer 3: real observation** | `status_table.py` | Reject deceptive monitoring, expose hidden failure | Inspect the core-loop logs, surface `🟢 POLLING` / `🔴 NO DNS` |

## What you can do right now

**Run this in your own WSL to check**:

```bash
dig @10.0.0.1 google.com +time=2 +tries=1
```

If you see `timed out`, your dev box has the same dangling-DNS problem.

**Pin WSL's DNS permanently (one sudo + one restart)**:

**Step 1** — edit `wsl.conf` to stop WSL auto-generating `resolv.conf`:

```bash
sudo tee /etc/wsl.conf << 'EOF'
[network]
generateResolvConf = false
[interop]
enabled=true
appendWindowsPath=true
[boot]
systemd=true
EOF
```

**Step 2** — this is the critical one, restart WSL. In PowerShell:

```powershell
wsl --shutdown
```

**Step 3** — back in WSL, configure the upstream DNS for systemd-resolved:

```bash
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo tee /etc/systemd/resolved.conf.d/public-dns.conf << 'EOF'
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=8.8.4.4 1.0.0.1
EOF
sudo systemctl restart systemd-resolved
```

**Step 4** — verify:

```bash
resolvectl status | grep "DNS Servers"
# expect: DNS Servers: 8.8.8.8 1.1.1.1

dig google.com +short
# expect an IP
```

> ⚠️ **Don't skip Step 2 and jump to Step 3.** If WSL isn't restarted, `generateResolvConf = false` isn't active and WSL's daemon keeps overwriting `/etc/resolv.conf`, silently rolling back every change. And if you skip Step 3, under `systemd=true` systemd-resolved takes over DNS with no upstream — DNS fails a different way.

**Audit the process probes in your own systems**:

Check your Supervisor, PM2, or Kubernetes liveness probes — do they measure an integer in the process table (the PID), or a data round-trip that represents real business value? A liveness probe should verify the app's health, not just that the PID exists:

```yaml
livenessProbe:
  exec:
    command: ["curl", "-f", "http://localhost:8080/health"]
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

So that your app detects a DNS problem the moment it happens — instead of trusting a live PID to prove it's healthy.
