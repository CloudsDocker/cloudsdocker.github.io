---
title: 'Stop Port-Forwarding Through Windows: Give WSL2 Its Own Tailscale Node'
header:
    image: /assets/images/bg/adfasdfasdf.jpg
date: 2026-09-26
tags:
 - wsl2
 - tailscale
 - ollama
 - systemd
 - gpu
permalink: /blogs/tech/en/wsl2-ollama-tailscale-gpu-inference
lang: en
layout: single
category: tech
---
# Stop Port-Forwarding Through Windows: Give WSL2 Its Own Tailscale Node

*Cut out Hyper-V virtual switch bridges and host firewall scripts by treating your Linux guest as an independent network peer.*

Run `tailscale status` on your remote laptop. If you only see one IP for your entire Windows rig, you are likely maintaining fragile Windows port proxies you do not actually need.

Every typical guide for exposing a WSL2 service across a local network follows the same tedious recipe: write a PowerShell startup script, add a `netsh interface portproxy` rule to map a Windows port to WSL2's internal virtual network IP, and poke an inbound hole through the Windows Defender firewall. By the end of this note, you will have Ollama serving GPU inference directly from WSL2 to any client on your private network without touching a single Windows firewall rule or port proxy.

### 🏗️ Why WSL2 Belongs Directly on Your Tailnet

When WSL2 originally launched, it lacked native systemd support and relied on a dynamic virtual Ethernet switch behind Windows NAT. That architecture forced you to treat the Windows host as an edge proxy for Linux.

Since WSL2 added native systemd support, that constraint no longer exists. If you install Tailscale directly inside WSL2 and let systemd manage `tailscaled`, the Linux environment receives its own distinct 100.x.y.z Carrier-Grade NAT address on the tailnet:

```text
<WSL_TAILSCALE_IP>      wsl-node          (WSL2 instance, managing RTX 5080)
<HOST_TAILSCALE_IP>     host-machine      (Windows 11 host, same physical machine)
<CLIENT_TAILSCALE_IP>   remote-client     (Remote client machine)
```

| Architecture Property | Windows Port-Proxy Bridge | Direct WSL2 Tailscale Node |
|---|---|---|
| Network Hops | Client → Windows IP → WSL NAT → Linux | Client → WSL `tailscale0` |
| Windows Host Firewall | Inbound TCP rule required | Uninvolved |
| Dynamic IP Handling | Needs PowerShell re-bind script on reboot | Handled natively by Tailscale |
| Debugging Surface | Two distinct routing layers | Standard Linux network stack |

Traffic sent from the client hits the `tailscale0` virtual adapter inside WSL2 directly. Windows host networking never inspects, bridges, or filters the packets.

### 🛠️ Binding Ollama to the Tailnet Interface

By default, Ollama binds strictly to loopback (`127.0.0.1:11434`). To accept remote requests over the tailnet interface, you must configure `OLLAMA_HOST=0.0.0.0:11434`.

Open a systemd drop-in override:

```bash
sudo systemctl edit ollama
```

Add the environment variable inside the `[Service]` block alongside any existing flags you use (such as flash attention or KV cache configurations):

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Reload the supervisor and restart the unit:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify that the daemon socket opened across all interfaces:

```bash
ss -tlnp | grep 11434
# Expected: *:11434 (not 127.0.0.1:11434)
```

### 🧠 The Silent Parser Trap in systemd Overrides

During my initial setup, `ss` persistently returned `127.0.0.1:11434` despite multiple restarts. The culprit was a single-character typographical error: `Engironment=` instead of `Environment=`.

When systemd encounters an unrecognized directive key inside a `.service.d` drop-in file, it does not fail the unit or emit a warning. It silently drops the unrecognized line. Running `systemctl status ollama` returns a clean, green `active (running)` state.

> 🩸 **Warning:** systemd silently ignores unrecognized key names in override drop-in files. A service reporting an active status is never evidence that your configuration parameters were actually parsed.

Never debug systemd overrides by checking process status. Compare the raw drop-in file against the active process runtime environment table:

```bash
cat /etc/systemd/system/ollama.service.d/override.conf  # What you wrote
systemctl show ollama -p Environment                   # What systemd parsed
```

systemctl status tells you that the process is alive, not that your configuration took effect. If the variable is absent from `systemctl show`, your override syntax was discarded.

### Prove the Interface Locally Before Touching the Client

Before switching over to the client machine, run a local query against the WSL2 Tailscale IP rather than `localhost`:

```bash
curl -s http://<WSL_TAILSCALE_IP>:11434/api/tags
```

Receiving the model list JSON confirms two facts simultaneously: Ollama is actually listening on the `tailscale0` interface, and the Tailscale transport inside WSL2 is active. This isolation step guarantees that if connection issues arise on your laptop, the problem resides entirely in client-side routing rather than host configuration.

Once verified, invoke it from the client:

```bash
# Direct curl check
curl http://<WSL_TAILSCALE_IP>:11434/api/tags

# Or point your local CLI
export OLLAMA_HOST=http://<WSL_TAILSCALE_IP>:11434
ollama run <model-name>
```

You can also paste `http://<WSL_TAILSCALE_IP>:11434` directly into tools like Open WebUI or LM Studio as the server base URL.

### 🧭 The 16GB Memory Ceiling

An RTX 5080 provides 16GB of VRAM. A model like `qwen2.5:32b` requires roughly 19.4GB at 4-bit quantization. If you issue an inference call for a model exceeding your video memory, Ollama offloads the remaining layers to system RAM across the PCIe bus.

Tokens-per-second will collapse from snappy interactive text down to a crawl, often manifesting on remote clients as HTTP timeouts. For reliable latency across a private network, restrict remote workloads on a 16GB card to ~14B parameters, or select more aggressive quantization profiles.

> 📌 **Takeaway:** Running an independent Tailscale daemon inside WSL2 removes host-level proxy complexity, but remember that systemd overrides require runtime verification via `systemctl show`.

### The Open Problem: Cold Reboots

One edge case remains unverified: complete cold recovery after a full Windows host reboot.

You should confirm that the daemon is registered to boot automatically:

```bash
systemctl is-enabled tailscaled
```

Even with the unit enabled, a cold Windows restart triggers a fresh WSL initialization cycle. If WSL2 delays initializing its virtual network before `tailscaled` attempts IP reservation, does the node retain its exact Tailscale IP immediately, and does Ollama wait for that binding? If your cold boot sequence drops the `tailscale0` interface before Ollama binds, what watchdog order did you pin in systemd?
