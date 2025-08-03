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
> A room without books is like a body without a soul. - Marcus Tullius Cicero

# When Azure CLI Met RHEL EUS: A Tale of Two Repositories 🔄


Picture this: It's Friday afternoon, you're deploying your latest Azure infrastructure changes, and suddenly your trusty `az` command throws a tantrum. The Azure CLI refuses to upgrade, Python versions are arguing with each other, and somewhere in the depths of your terminal, EUS repositories are quietly chuckling at your predicament.

Welcome to the wild world of enterprise Linux, where stability meets innovation in the most interesting ways possible.

## The Plot Twist Nobody Saw Coming

Here's what happened to me last week. I was happily running Azure CLI commands on my RHEL 9.2 system when Microsoft dropped Azure CLI 2.75.0 with a seemingly innocent requirement: Python 3.12. Simple enough, right? Just update Python and move on.

**Narrator**: *It was not simple enough.*

```bash
$ yum install python3.12
No package python3.12 available.
Error: Unable to find a match: python3.12
```

Wait, what? This is RHEL 9! Python 3.12 should definitely be available. Time to investigate:

```bash
$ yum repolist
repo id                                                              repo name
codeready-builder-for-rhel-9-x86_64-eus-rhui-rpms                    Red Hat CodeReady Linux Builder for RHEL 9 x86_64 - Extended Update Support from RHUI (RPMs)
rhel-9-for-x86_64-appstream-eus-rhui-rpms                            Red Hat Enterprise Linux 9 for x86_64 - AppStream - Extended Update Support from RHUI (RPMs)
rhel-9-for-x86_64-baseos-eus-rhui-rpms                               Red Hat Enterprise Linux 9 for x86_64 - BaseOS - Extended Update Support from RHUI (RPMs)
```

Ah-ha! There's the culprit hiding in plain sight. See those three little letters scattered throughout? **EUS** - Extended Update Support. My system was locked in time, like a digital Rip Van Winkle.

## The EUS Revelation: When Stability Becomes a Prison

Extended Update Support isn't some obscure Linux feature that only beard-stroking sysadmins care about. It's actually one of the most ingenious solutions to a very real enterprise problem that affects millions of production systems worldwide.

### The Enterprise Dilemma

Imagine you're running a trading platform that processes millions of dollars per second. Your application is certified on RHEL 9.2, tested extensively, and has been running flawlessly for months. Then one day, a routine `yum update` pulls in RHEL 9.4 with subtle changes that cause your trading algorithms to behave differently. The result? Potential financial losses that make your head of risk management break out in cold sweats.

This is where EUS comes to the rescue, like a time-traveling superhero with a very specific superpower.

### EUS: The Digital Time Capsule

Extended Update Support essentially creates a "snapshot" of your RHEL minor version and says: "This is your world now. You'll get security patches and critical fixes, but no surprises." It's like living in a neighborhood where the houses get security upgrades and fresh paint, but the street layout never changes.

Here's the beautiful part: EUS repositories are maintained separately for each supported minor version. So while the main RHEL 9 repositories march forward to 9.5, 9.6, and beyond, your EUS repositories stay frozen at 9.2, carefully curated to maintain perfect stability.

```bash
# Regular repos (the fast lane)
rhel-9-for-x86_64-baseos-rpms          # Always latest (9.5, 9.6, etc.)

# EUS repos (the stability lane)  
rhel-9.2-for-x86_64-baseos-eus-rpms    # Forever 9.2
```

## The Python 3.12 Predicament: When Innovation Meets Immutability

Now here's where it gets interesting. Python 3.12 was released in October 2023, but it only became available in RHEL starting with version 9.4. My system, locked in the EUS time capsule of 9.2, had no idea this shiny new Python version even existed.

This creates what I like to call the "Innovation Paradox":
- **Azure CLI** (cloud-native, fast-moving): "I need Python 3.12 for all these cool new features!"
- **RHEL EUS** (enterprise-stable, slow-moving): "Python 3.11 has been working fine for months. Why change?"

It's like trying to run a Tesla's software stack on a perfectly maintained 1990s Honda Civic. Both are excellent in their own right, but they have very different philosophies about change.

## The Moment of Truth: Two Paths Diverged

Microsoft's support team presented me with two elegant solutions, each with its own personality:

### Option 1: The Surgical Strike (Enable Non-EUS Repos)

This is the "have your cake and eat it too" approach. By temporarily switching to non-EUS repositories, you can selectively install Python 3.12 while keeping your OS at 9.2.

**The Good**: Minimal disruption, surgical precision
**The Drama**: You're essentially creating a hybrid system with packages from different timelines

```bash
# The transformation spell
subscription-manager repos --disable="*eus*"
subscription-manager repos --enable="rhel-9-for-x86_64-baseos-rpms"
subscription-manager repos --enable="rhel-9-for-x86_64-appstream-rpms"

# Install Python 3.12
yum install python3.12

# Optionally switch back to EUS
subscription-manager repos --enable="*eus*"
subscription-manager repos --disable="rhel-9-for-x86_64-baseos-rpms"
subscription-manager repos --disable="rhel-9-for-x86_64-appstream-rpms"
```

### Option 2: The Great Leap Forward (Upgrade to RHEL 9.4)

This is the "embrace the future" approach. Upgrade your entire system to RHEL 9.4, where Python 3.12 lives naturally.

**The Good**: Clean, consistent, future-proof
**The Commitment**: You're leaving the EUS safety net for 9.2 behind

```bash
# The evolution command
subscription-manager repos --disable="*eus*"
yum update
# System becomes RHEL 9.4
```

## The Hidden Wisdom: Why This Matters Beyond Azure CLI

This isn't just about Azure CLI or Python versions. This scenario perfectly illustrates one of the most fundamental tensions in modern IT infrastructure:

**Stability vs. Innovation**

Every enterprise faces this daily:
- Your security team wants the latest patches (innovation)
- Your compliance team wants zero changes (stability)  
- Your developers want the newest tools (innovation)
- Your operations team wants predictable systems (stability)

EUS repositories represent Red Hat's sophisticated answer to this eternal struggle. They're not just technical constructs; they're peace treaties between competing organizational needs.

## The Plot Resolution: What I Actually Did

After pondering the philosophical implications (and checking with our change management board), I chose Option 1 with a twist. Here's my battle-tested approach:

```bash
# 1. Document current state
yum repolist > repos_before.txt
rpm -qa > packages_before.txt

# 2. Temporarily switch to non-EUS
subscription-manager repos --disable="*eus*"  
subscription-manager repos --enable="rhel-9-for-x86_64-appstream-rpms"

# 3. Install only what I need
yum install python3.12 python3.12-pip

# 4. Install Azure CLI with new Python
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 5. Switch back to EUS for future stability
subscription-manager repos --enable="*eus*"
subscription-manager repos --disable="rhel-9-for-x86_64-appstream-rpms"

# 6. Verify everything works
az --version
```

**Result**: Azure CLI 2.75.0 running happily with Python 3.12, while my system remains fundamentally rooted in the stability of RHEL 9.2 EUS.

## The Bigger Picture: Lessons for Modern Infrastructure

This experience taught me something profound about modern infrastructure management:

### 1. **Repositories Are Philosophies**
Every repository represents a different approach to change management. EUS says "stability first," while standard repos say "progress first." Neither is wrong; they serve different masters.

### 2. **Hybrid Approaches Work** 
You don't always have to choose between all-stability or all-innovation. Sometimes the smartest move is a surgical strike that gets you exactly what you need.

### 3. **Documentation Is Your Time Machine**
Before making any repository changes, document your current state. Future you will thank present you when something unexpected happens.

### 4. **Understanding the 'Why' Changes Everything**
Once I understood why EUS exists and what problem it solves, the entire situation made sense. It wasn't a barrier; it was a feature working exactly as designed.

## The Technical Archaeology: What Your `yum repolist` Really Tells You

Let's decode what my repository list was actually saying:

```bash
rhel-9-for-x86_64-baseos-eus-rhui-rpms
```

Breaking this down:
- `rhel-9`: RHEL version 9 family
- `x86_64`: Architecture (Intel/AMD 64-bit)
- `baseos`: Core operating system packages
- `eus`: Extended Update Support (the key insight!)
- `rhui`: Red Hat Update Infrastructure (Azure-specific delivery)
- `rpms`: Package format

Each piece tells a story about how your system is configured and what its update philosophy is.

## The Future-Proofing Strategy

Here's what I'm implementing going forward:

### 1. **Repository Awareness**
Always check `yum repolist` when mysterious package availability issues arise. Those three letters (EUS) can save you hours of debugging.

### 2. **Hybrid Repository Strategy**
For critical updates that aren't available in EUS, temporarily switch repositories, install what you need, then switch back. Document everything.

### 3. **Change Management Integration**
Make repository strategy part of your change management process. EUS vs. non-EUS isn't just a technical decision; it's a business decision.

### 4. **Monitoring and Alerting**
Set up monitoring to alert when packages you depend on require newer base OS versions. This gives you lead time to plan upgrades.

## The Epilogue: Why This Story Matters

This isn't just another "how I fixed a Linux problem" story. It's a microcosm of how modern enterprise infrastructure works. Every day, thousands of organizations face similar decisions: Do we prioritize stability or innovation? Do we upgrade everything or just what we need?

The beautiful thing about technologies like EUS is that they don't force you to choose. They give you options, each with clear trade-offs, and let you make informed decisions based on your specific needs.

My Azure CLI is now happily running with Python 3.12, my system remains stable on RHEL 9.2 EUS, and I've gained a deeper appreciation for the thoughtful engineering that goes into enterprise Linux distributions.

## The Practical Takeaways

If you find yourself in a similar situation:

1. **Don't panic** - This is a common scenario with well-understood solutions
2. **Check your repositories first** - `yum repolist` is your friend
3. **Understand your constraints** - What does your organization require for stability vs. innovation?
4. **Document everything** - Your future self will thank you
5. **Test thoroughly** - Hybrid approaches work, but they need validation

The next time someone tells you that enterprise Linux is boring, show them this story. Behind every seemingly simple package installation lies a fascinating world of engineering trade-offs, organizational psychology, and the eternal tension between stability and progress.

And remember: when Azure CLI meets RHEL EUS, it's not a conflict—it's an opportunity to understand how modern infrastructure really works.

---

*Have you faced similar repository conflicts in your infrastructure? What creative solutions did you discover? Share your stories in the comments below.*