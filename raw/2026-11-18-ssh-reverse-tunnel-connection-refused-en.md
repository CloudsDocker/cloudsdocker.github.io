---
title: The Last Line Lies — Root-Causing a Connection Refused in an SSH Reverse Tunnel
header:
    image: /assets/images/hd_linux_tips.jpg
date: 2026-11-18
tags:
 - ssh
 - reverse-tunnel
 - networking
 - debugging
 - wsl
permalink: /blogs/tech/en/ssh-reverse-tunnel-connection-refused
layout: single
category: tech
---

> "When you have eliminated the impossible, whatever remains, however improbable, must be the truth." — Arthur Conan Doyle, *The Sign of Four*, Sherlock Holmes

# The Last Line Lies — Root-Causing a Connection Refused in an SSH Reverse Tunnel

*From "where the error shouts" to "where the root cause hides" — the line that separates a senior from a principal, visible in a single screen of logs.*

I killed an `autossh` tunnel I'd been keeping open by hand. A few minutes later I typed `ssh home-wsl` on my MacBook, watched forty lines of `debug1:` scroll past, and landed on this:

```
kex_exchange_identification: Connection closed by remote host
Connection closed by UNKNOWN port 65535
```

`kex_exchange_identification` — the handshake died during key exchange. Search for *that* line and you'll be dragged into threads about "incompatible SSH versions," "algorithm negotiation failure," "MTU/firewall cutting the handshake." You'll spend an evening tuning `KexAlgorithms` and running `tcpdump` chasing a phantom MTU problem.

**All wrong.** The actual failure is a line further *up* the log — and it isn't really a "failure" at all. It's a direct, by-design consequence of something I did with my own hands.

This post is about that one screen of logs. You'll walk away with three things:

- **A hard rule for reading logs**: scan top-down for the *first* `failed`. The last line is usually the autopsy report, not the killer.
- **An architectural intuition**: a reverse tunnel's listening port has its lifecycle *bound to a single process*. The process dies, the port dies. That's not a bug.
- **A senior-vs-principal dividing line**: the gap between "I can start it by hand" and "it stays alive on its own" is exactly one `systemd` service wide.

> Note: the public IP below is replaced with the documentation-reserved address `203.0.113.10`; the topology is a generic reverse-SSH-tunnel pattern.

---

## Draw the terrain first: one command, two connections, three machines

My situation is a common one. The corporate laptop allows only outbound 443 and forbids VPN software. My home dev box is WSL, stuck behind NAT with no public IP. In between sits a cheap cloud VM with a public IP, acting as a jump host (I'll call it `spring-board`). The goal: from any 443-only network, type `ssh home-wsl` and land inside home WSL as if it were local.

```
corporate laptop ──443──▶  spring-board (203.0.113.10)  ──reverse tunnel──▶  home WSL (sshd:2222)
  ssh home-wsl              public jump, sshd on :443          WSL dials OUT and holds the door
  (ProxyJump)
```

The detail everyone glosses over: **traffic flows one way, but the tunnel is built the other way.**

- At use time: laptop → jump → WSL. Traffic goes *inward*.
- At setup time: **home WSL dials outward**, opening a "door home" on the jump host. A NAT'd box can't be reached from outside, but it can reach out — that's the entire meaning of "reverse."

That "door home" is concretely a listener on the jump host at `127.0.0.1:2200`. Who holds it open? A single command running on home WSL:

```bash
autossh -M 0 -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
  -i ~/.ssh/id_ed25519_tunnel \
  -R 127.0.0.1:2200:localhost:2222 -p 443 tunnel@203.0.113.10
```

Remember this line, especially `-R 127.0.0.1:2200:localhost:2222`. Every piece of causality converges on it.

> In one sentence: a reverse tunnel isn't "the jump host dialing home." It's "home nailing a door into the jump host's inner wall." The door lives and dies with whoever nailed it.

---

## Read the log as three acts: most of the text is there to cover for the killer

`ssh home-wsl -v` emits forty-odd lines, but it's really **two ssh processes** talking over each other. Why two? Because `ProxyJump` is nested by nature:

```
debug1: Setting implicit ProxyCommand from ProxyJump: ssh -W '[%h]:%p' usdream-jump
debug1: Executing proxy command: exec ssh -W '[127.0.0.1]:2200' usdream-jump
```

The **outer ssh** (the one you typed) doesn't connect to the jump host itself. It forks an **inner ssh** whose job is to "connect to the jump host, authenticate, then from the jump host's point of view dial `127.0.0.1:2200`," and it treats that pipe as its own raw socket. So the two `OpenSSH_10.5p1` banners and two config reads in the log aren't spam — they're two processes each printing once.

Slice it into three acts and the signal jumps out:

**Act 1 · the outer ssh hands off the work (first few lines)**
`%h/%p` get filled from the config's `HostName 127.0.0.1 / Port 2200`. Note that this `127.0.0.1` resolves *on the jump host*, not on your Mac's loopback. The outer ssh now just waits for a pipe.

**Act 2 · the inner ssh connects and authenticates — all green**

```
debug1: Connecting to 203.0.113.10 port 443.   →   Connection established.
debug1: Host '[203.0.113.10]:443' is known and matches the ED25519 host key.
debug1: Server accepts key: .../id_ed25519_usdream_wsl
Authenticated to 203.0.113.10 ([203.0.113.10]:443) using "publickey".
```

TCP is up, the host key matches, publickey auth passes. **The jump host layer — network and identity both — is flawless.** The value of this act isn't that it succeeded; it's that it *eliminates a whole swath of hypotheses* for you: not 443 being blocked, not a wrong key, not a dead jump host, not a changed host key. This is where Holmes earns his keep — with the impossibles crossed off, the root cause can only be downstream.

**Act 3 · the real killer (the fatal four lines)**

```
debug1: channel_connect_stdio_fwd: 127.0.0.1:2200
channel 0: open failed: connect failed: Connection refused     ← first failed, the real root cause
stdio forwarding failed
kex_exchange_identification: Connection closed by remote host
Connection closed by UNKNOWN port 65535                        ← the line you fixated on first
```

After the inner ssh authenticates, it issues your `-W` request to the jump host: "dial your own `127.0.0.1:2200` for me." The jump host's kernel calls `connect(127.0.0.1:2200)` and gets an **instant** RST, because **no process is listening** on that port. Hence: `Connection refused`.

The three lines after it are all autopsy. The pipe collapses → the inner ssh exits → the outer ssh's "raw socket" dies → the outer ssh, before it can even run its own key exchange, finds the far end gone and cries `kex_exchange_identification: Connection closed`. The `UNKNOWN port 65535` is because the far end is a pipe, not a real socket, so ssh can't read a port number and prints a placeholder.

| Log line you see | What it's actually saying | Trust it? |
|---|---|---|
| `Connection refused` (first failed) | Reached the host, but nothing's listening | **Yes — this is the killer** |
| `stdio forwarding failed` | The `-W` pipe can't be built | Direct consequence |
| `kex_exchange_identification: Connection closed` | Outer ssh finds the pipe dead | Chain reaction — **ignore** |
| `Connection closed by UNKNOWN port 65535` | Far end is a pipe, no port number | Placeholder noise — **ignore** |

> **The First-Failed Law**: in a screen of errors, only the first `failed`/`refused` from the top carries information; every line below it is just restating "because that one died, I died too." Reading a log is archaeology, not reading the news — don't reason backward from the headline.

---

## Why "killing autossh" *had* to produce this

Now connect Act 3's `127.0.0.1:2200 refused` back to that `autossh -R ...` from the first section.

`-R 127.0.0.1:2200:localhost:2222` means: **make the jump host listen on its own `127.0.0.1:2200`; any traffic that connects there rides the already-established reverse tunnel back down to home WSL's `localhost:2222`** (WSL's own sshd).

The crux: **that listener is opened by the autossh process.** It isn't a resident service on the jump host, it isn't in `/etc/`, it doesn't survive a reboot of the jump host. It's a byproduct of a client connection —

> autossh alive → `127.0.0.1:2200` is `LISTEN`;
> autossh dead → that listener vanishes from the jump host *the same instant*.

The command I carelessly killed was the only nail holding the "door home" shut. Pull the nail and there isn't even a hole left in the wall. So when the jump host calls `connect(2200)`, the kernel honestly reports: nobody's here. `Connection refused` isn't a malfunction — it's **the only correct answer the system can give after I dismantled the entrance myself.**

There's a quiet amplifier hiding here too: `-o ExitOnForwardFailure=yes` in the command. It means "if the reverse port doesn't come up, autossh would rather die than pretend it's alive." The upside is you never get the zombie state of "process running, port empty" — but it's also a reminder: **this tunnel's health is all-or-nothing; there is no 'up but useless'.**

```
Mac ──443──▶ spring-board:443 (sshd, auth OK)
                 │
                 └─ needs to dial 127.0.0.1:2200 ──┐
                                                   who provides this listener?
home WSL ──autossh -R 127.0.0.1:2200:localhost:2222──▶ that one (which I killed)
```

**The naive read**: "`ssh home-wsl` won't connect — must be the jump host or my Mac config."
**The seasoned insight**: the log already *proves* the jump host and the Mac are correct; the failure therefore points precisely at **the one link in the chain that's kept alive by a process** — and a reverse tunnel has exactly one such link: that autossh at home. One direction, no guessing.

---

## The fix: prove the cause in 30 seconds, then turn it into something you never touch

**Step 1 · prove causality (one command on home WSL):**

```bash
# home WSL: bring the tunnel back up
autossh -M 0 -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
  -i ~/.ssh/id_ed25519_tunnel \
  -R 127.0.0.1:2200:localhost:2222 -p 443 tunnel@203.0.113.10 &

# from any box that can log into the jump host, confirm the listener is back:
ssh spring-board 'ss -tlnp | grep 2200'   # expect: 127.0.0.1:2200 ... LISTEN
```

See `LISTEN`, and `ssh home-wsl` on the Mac works instantly — **without touching a single line of Mac config**, which re-confirms Act 2's verdict: the laptop end was right all along.

Here's a detail worth points in an interview: `Connection refused` and `Connection timed out` are two entirely different diseases.

| Symptom | At the kernel | Meaning | Where to look |
|---|---|---|---|
| **Instant** `Connection refused` | Got an RST | Packet reached the host, nothing listening | the service / listening process |
| **Hangs then** `timed out` | Got nothing back | Packet was dropped, host never answered | firewall / security group / routing |

Mine was an **instant refused**, so the root cause snaps straight to "the listener is gone" — no need to even look at security groups or 443. Telling these two apart on sight saves you half a night of packet captures.

**Step 2 · promote "tribal knowledge" into an "engineering artifact":**

The real problem was never "the tunnel died." It's that **this tunnel's survival depended on me remembering to start it by hand.** That's textbook tribal knowledge — an ops action that lives only in my head, kept alive by muscle memory. It will eventually break from a reboot, a slip of the hand, or a sleep cycle, and when it breaks, nobody will know.

The principal's move is to pin it down as a self-healing `systemd` service:

```ini
# home WSL: /etc/systemd/system/reverse-tunnel.service
[Unit]
Description=Reverse SSH tunnel to spring-board
After=network-online.target
Wants=network-online.target

[Service]
User=phray
ExecStart=/usr/bin/autossh -M 0 -N -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new \
  -i /home/phray/.ssh/id_ed25519_tunnel \
  -R 127.0.0.1:2200:localhost:2222 -p 443 tunnel@203.0.113.10
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now reverse-tunnel
ssh spring-board 'ss -tlnp | grep 2200'   # verify: the listener comes back on its own
```

`Restart=always` plus `ServerAliveInterval` fixes exactly the trap I fell into today: it starts on boot and reconnects after a network drop or sleep via keepalive probes. I never again need to "remember to start one by hand and stop one by hand."

But there's a WSL-specific reef I have to call out: **WSL is only alive while Windows keeps the distro up.** However elegant your `systemd` service, if the WSL distro itself isn't awake, the service is a dead letter. For a tunnel that truly survives boot, you also need a Windows Task Scheduler job at login that runs `wsl.exe -d <distro> ...` to bring the distro up. **A self-healing chain is only as strong as its weakest link — and the weakest link is usually in the host layer you weren't watching.**

> This is a sibling to my earlier post, *An SSH Login Failure That Made Me Rethink Linux's Permission Design Philosophy*. Last time I tripped on **permissions** (the philosophy behind file modes); this time on **lifecycle** (what a listening port is actually attached to). SSH keeps hitting me in a different spot each time, but it keeps teaching the same lesson: don't trust the line that shouts the loudest.

---

## Three sentences to close

| Layer | The one sentence I learned today |
|---|---|
| Reading logs | Scan top-down for the first `failed`; the last line is usually the autopsy |
| Understanding architecture | A reverse tunnel's listener is bound to the autossh process — process dies, port dies |
| Doing ops | "I can run it by hand" ≠ "it's set up"; only a `Restart=always` service is an engineering artifact |

### Do this today

1. Count how many "alive only because I remember to start them" processes live in your own setup — tunnels, port-forwards, `kubectl port-forward`, throwaway `ssh -L`. Each one is a mine that goes off on your busiest day.
2. Take the most critical one and, today, rewrite it as a `systemd` service (or equivalent self-healing mechanism). While you're at it, add an `ss -tlnp | grep <port>` verification line to your runbook.
3. Next time a screen of SSH errors scrolls past, don't search the last line. Rerun with `-v`, scan top-down for the first `failed`, circle it, *then* decide where to look.

*The line that shouts the loudest is usually the furthest from the truth; the truth tends to sit quietly upstream, waiting for someone willing to read from the top.*
