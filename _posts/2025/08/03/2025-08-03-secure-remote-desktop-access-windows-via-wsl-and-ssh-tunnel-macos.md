---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  Secure Remote Desktop Access Windows via WSL and SSH Tunnel macOS
date: 2025-08-03
tags:
    - tech
permalink: /blogs/tech/en/secure-remote-desktop-access-windows-via-wsl-and-ssh-tunnel-macos
layout: single
category: tech
---
> Our greatest weakness lies in giving up. The most certain way to succeed is always to try just one more time. - Thomas A. Edison

# 🛠️ Secure Remote Desktop Access to Windows via WSL and SSH Tunnel on macOS

> *"How I securely accessed my Windows desktop through WSL and SSH Tunnel from my Mac, and what I learned along the way."*
> — by \[Your Name], August 2025

---

## 🔒 Why SSH Tunnel + RDP?

When you're working across devices — say, developing on a **MacBook** while occasionally needing full GUI access to a **Windows machine** — you might default to enabling RDP (Remote Desktop Protocol) and opening it to the world. **Don’t.**
Instead, **SSH tunneling** gives you an encrypted, firewall-friendly way to access your Windows desktop — without exposing the RDP port (3389) to the internet.

In this guide, I’ll walk you through a practical use case: I’m on a **MacBook**, and I want to connect to a **Windows 11 machine**, securely, by tunneling through its **WSL2 (Ubuntu)** instance — where I already have SSH access.

---

## 🧱 System Architecture Overview

Here’s what we're building:

```
MacBook (Microsoft Remote Desktop)
        |
        |  SSH (Port 8222) with Tunnel
        v
Remote Host (Windows 11 + WSL2 Ubuntu)
        |
        |  Forwarded RDP traffic (port 3389)
        v
Windows Desktop (via 127.0.0.1:3389)
```

---

## ⚙️ Key Components Explained

### ✅ SSH Tunnel

An **SSH tunnel** securely forwards local ports to a remote host over an encrypted channel. Think of it as a VPN-like pipe — but lighter, and easier to manage.

```bash
ssh -L local_port:remote_host:remote_port user@remote -p port
```

In our case:

```bash
ssh -i ~/.ssh/id_aidrapc_macpro -p 8222 \
  -L 3390:172.30.192.1:3389 phray@121.209.151.71
```

This opens an SSH session into WSL and creates a tunnel from `localhost:3390` (on Mac) to `Windows:3389` (RDP).

---

### ✅ Windows RDP (Remote Desktop Protocol)

RDP is the native Microsoft remote desktop solution. It runs on port `3389` and allows full GUI access. But exposing it directly to the internet is dangerous.

### ✅ WSL (Windows Subsystem for Linux)

WSL allows Linux to run on Windows natively. We use it as a secure landing pad: we connect to WSL over SSH, and from there access Windows resources.

---

## 🧪 The Problem: Tunnel Worked, But RDP Hung

After successfully running:

```bash
ssh -i ~/.ssh/id_aidrapc_macpro -p 8222 -L 3390:172.30.192.1:3389 phray@121.209.151.71
```

And opening **Microsoft Remote Desktop** on macOS with:

* **PC name**: `localhost:3390`
* **User**: my Windows credentials

…I was stuck on *"Connecting..."* forever. 😒

---

## 🔍 Troubleshooting Steps

### 1. ✅ SSH Tunnel Verified

If you see the Ubuntu login welcome message (`Welcome to Ubuntu 24.04.2 LTS`), your tunnel is alive. So the issue isn’t SSH.

### 2. ❌ No Response from RDP

I ran this inside the WSL terminal:

```bash
nc -zv 172.30.192.1 3389
```

Got nothing — not even a timeout error. That told me the **Windows RDP port wasn’t reachable from WSL**.

---

## 🧯 Fixing the Root Cause

### ✅ Step 1: Enable RDP in Windows

Go to:

```
Settings → System → Remote Desktop → Enable Remote Desktop
```

Ensure it’s **enabled** and the current user is allowed to connect.

---

### ✅ Step 2: Open RDP Port in Windows Firewall

Run the following in **PowerShell (Admin)**:

```powershell
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
```

This opens all required rules for local and remote RDP connections.

---

### ✅ Step 3: Confirm Windows IP from WSL

Run inside WSL:

```bash
cat /etc/resolv.conf
```

You’ll typically see:

```
nameserver 172.30.192.1
```

This IP is your **Windows host**, from the WSL perspective.

Now run:

```bash
nc -zv 172.30.192.1 3389
```

If you see:

```
Connection to 172.30.192.1 3389 port [tcp/ms-wbt-server] succeeded!
```

You’re good to go!

---

## 🖥️ Final RDP Setup on macOS

1. Launch **Microsoft Remote Desktop**.
2. Add a new PC with:

   * **PC Name**: `127.0.0.1:3390`
   * **Username/Password**: your Windows credentials (not WSL).
3. Connect and enjoy full Windows desktop in a secure tunnel!

---

## 💡 Bonus: Run Tunnel in Background

To avoid an open terminal window, use:

```bash
ssh -fN -i ~/.ssh/id_aidrapc_macpro -p 8222 -L 3390:172.30.192.1:3389 phray@121.209.151.71
```

* `-f`: run in background
* `-N`: don’t execute remote commands

---

## 🧠 What You (Should) Learn

| Concept         | Why it matters                                            |
| --------------- | --------------------------------------------------------- |
| SSH Tunnel      | Encrypts traffic, avoids open firewall ports              |
| WSL             | Useful Linux shell on Windows, great for DevOps workflows |
| RDP             | Standard GUI remote access on Windows                     |
| Port forwarding | Foundation of secure remote system access                 |

---

## 🏁 Final Thoughts

This method is **safer than directly exposing RDP**, requires minimal setup, and works beautifully when configured correctly. And if you're like me — working across platforms and valuing security — it's a great daily-driver tool to have in your pocket.

Let me know in the comments — do you tunnel into your machines like this? Any clever tricks or failures you’ve learned from?

---

💬 *Want more security-first remote access tricks like this? Subscribe to my newsletter.*
📩 *Or follow me on [GitHub](https://github.com/) and [Twitter/X](https://x.com/) for more dev-friendly writeups.*
