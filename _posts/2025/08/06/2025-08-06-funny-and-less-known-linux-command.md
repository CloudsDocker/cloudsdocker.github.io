---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  Linux Command-Line Tricks That Will Make You Feel Like a Power User  🚀
date: 2025-08-06
tags:
    - tech
    - DevOps
    - Enterprise Security
    - GitHub
    - SAML SSO 
permalink: /blogs/tech/en/funny-and-less-known-linux-commands
layout: single
category: tech
---

> Happiness is not something ready made. It comes from your own actions. - Dalai Lama

# 14 Linux Command-Line Tricks That Will Make You Feel Like a Power User 🚀

If you spend any time in the terminal, you know there’s always something new to learn. Whether you’re a developer, sysadmin, or just a curious tinkerer, mastering a few clever Linux commands can save you hours and make you look like a wizard to your peers. Here are 14 practical, sometimes surprising, and always useful command-line tricks that will level up your Linux game!

---

## 1. Quickly Serve Any Directory Over HTTP

Ever needed to share files with a colleague or test a static website? You can spin up a web server in seconds:

```bash
python3 -m http.server 8080
```
Just point your browser to `http://localhost:8080` and you’re live!

---

## 2. Find the 10 Largest Files in a Directory Tree

Running out of disk space? Find the culprits fast:

```bash
find . -type f -exec du -h {} + | sort -rh | head -n 10
```
This command lists the 10 biggest files, sorted by size, so you know what to clean up.

---

## 3. Show Running Processes as a Tree

Visualize process relationships with:

```bash
pstree -p
```
It’s like a family tree for your running programs!

---

## 4. Repeat the Last Command with `sudo`

Typed a command and forgot `sudo`? No need to retype:

```bash
sudo !!
```
This reruns your last command with superuser privileges.

---

## 5. Show Only Directories (Not Files)

Want a clean list of just directories?

```bash
ls -d */
```
Perfect for scripting or just keeping things tidy.

---

## 6. Count Files by Extension

How many Python files are in your project?

```bash
find . -type f -name "*.py" | wc -l
```
Swap out `*.py` for any extension you like.

---

## 7. Find and Delete Empty Files

Clear out those zero-byte files:

```bash
find . -type f -empty -delete
```
A quick way to keep your workspace clean.

---

## 8. Monitor File Changes in Real Time

Watch logs or any file as it grows:

```bash
tail -f /var/log/syslog
```
Great for debugging or monitoring.

---

## 9. Show Top Memory or CPU Consuming Processes

Find resource hogs instantly:

```bash
ps aux --sort=-%mem | head -n 11   # Top memory users
ps aux --sort=-%cpu | head -n 11   # Top CPU users
```

---

## 10. Find Files Modified Recently

Track down what’s changed in the last hour or day:

```bash
find . -type f -mmin -60      # Modified in last 60 minutes
find . -type f -mtime -1      # Modified in last 1 day
```

---

## 11. Get Your Public IP Address

Need to know your external IP?

```bash
curl ifconfig.me
```
Or try `curl -s https://ipinfo.io/ip` for another source.

---

## 12. Show All Open Network Ports

See what’s listening on your system:

```bash
sudo ss -tulnp
```
A modern replacement for `netstat`.

---

## 13. Find and Replace Text Recursively

Bulk update text across many files:

```bash
grep -rl "oldtext" . | xargs sed -i 's/oldtext/newtext/g'
```
Be careful—this is powerful!

---

## 14. Generate a Random Password

Need a strong password in a pinch?

```bash
openssl rand -base64 16
```
Instant, secure, and ready to use.

---

## Bonus: Combine Commands for Superpowers

Want to find all `.azw3` files and get their total size?

```bash
find . -type f -name "*.azw3" -exec du -ch {} + | grep total$
```
This gives you a neat summary at the end.

---

## Final Thoughts

The Linux command line is a treasure trove of productivity boosters. Try these out, tweak them for your workflow, and don’t be afraid to explore further. Every command you master is another tool in your digital toolbox!

**What’s your favorite Linux trick? Share it in the comments below!**

---
