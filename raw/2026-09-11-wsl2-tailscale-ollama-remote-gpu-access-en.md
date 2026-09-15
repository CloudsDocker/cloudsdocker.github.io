# Exposing WSL2 Ollama over Tailscale to a MacBook (remote GPU inference)

Goal: use the RTX 5080 in a WSL2 (Windows 11) box from a MacBook Air on the
same tailnet, by hitting Ollama running inside WSL2 remotely.

## Key fact that made this easy

This WSL2 instance runs its **own Tailscale node via systemd**, separate
from the Windows host's Tailscale node:

```
100.85.1.56     aidra-studio-wsl     (WSL2, this box)
100.124.38.9    aidra-studio         (Windows host, same physical machine)
100.121.102.62  toddzhangs-macbook-air
```

Because WSL2 is a first-class tailnet peer with its own IP, there is
**no need for**:
- `netsh interface portproxy` (Windows -> WSL2 NAT bridging)
- Windows Firewall inbound rules

Traffic from the Mac reaches the `tailscale0` interface *inside* WSL2
directly. This is the newer/simpler pattern vs. the classic "Tailscale
only on Windows, WSL is NATed behind it" setup most guides assume.

## The fix

Ollama defaults to binding `127.0.0.1:11434` only. Needed
`OLLAMA_HOST=0.0.0.0:11434` so it listens on all interfaces (tailnet
included):

```bash
sudo systemctl edit ollama
```

Add inside the `[Service]` block (alongside any existing `Environment=`
lines like `OLLAMA_FLASH_ATTENTION`, `OLLAMA_KV_CACHE_TYPE`, etc.):

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify:

```bash
ss -tlnp | grep 11434
# want: *:11434   (not 127.0.0.1:11434)
```

## Troubleshooting: the silent typo trap

First attempt didn't work — `ss` still showed `127.0.0.1:11434` after
restart. Cause: typed `Engironment="OLLAMA_HOST=..."` (typo) instead of
`Environment=`.

**systemd does not error on an unrecognized directive key inside a
`.service.d` override — it just silently ignores that line.**
`systemctl status ollama` still reported `active (running)` with zero
complaints. This is the trap: status-looks-fine does not mean
config-took-effect.

The actual verification is comparing the *effective* environment against
the file:

```bash
cat /etc/systemd/system/ollama.service.d/override.conf   # what you wrote
systemctl show ollama -p Environment                      # what's actually active
```

If the var you just added is missing from `systemctl show` output, the
override didn't parse — go re-read the file for typos, don't just restart
again and hope.

Fixed the typo -> `daemon-reload` -> `restart` -> `ss` now shows `*:11434`.

## Confirm reachable before testing from the Mac

From the WSL box itself, hit its own tailnet IP (not localhost) to prove
it's actually listening on that interface and not just "on all interfaces
in theory":

```bash
curl -s http://100.85.1.56:11434/api/tags
```

Got back the model list JSON — confirmed reachable over tailnet before
touching the Mac at all. Cheap sanity check that isolates "is Ollama
actually exposed" from "is something wrong on the Mac side."

## Client side (MacBook Air)

```bash
curl http://100.85.1.56:11434/api/tags     # sanity check first
export OLLAMA_HOST=http://100.85.1.56:11434
ollama run <model-name>
```

Or point any Ollama-compatible client (Open WebUI, LM Studio, etc.) at
`http://100.85.1.56:11434` as the base URL.

## GPU memory sizing note

RTX 5080 = 16GB VRAM. A `qwen2.5:32b` model (~19.4GB) doesn't fit — forces
CPU offload for the overflow, which is very slow. For responsive remote
inference from the Mac, stay around 14B params or use a more aggressive
quant of a larger model. (This matches an earlier diagnosis this week of
Ollama timeouts caused by exactly this VRAM overflow.)

## Persistence caveat (not yet verified)

Haven't confirmed this survives a full Windows/WSL restart end to end.
Should check:

```bash
systemctl is-enabled tailscaled
```

If `tailscaled` isn't `enabled`, the WSL2 tailnet IP won't come back
automatically after a reboot, and the whole setup silently breaks until
someone notices and manually restarts it.

> 待验证 / unresolved: haven't tested a full reboot cycle (Windows restart
> -> WSL cold start -> does tailscaled auto-start -> does it get the same
> IP -> does ollama.service come up with the override intact). Assuming
> yes based on `enabled` unit status, not actually verified end to end.
