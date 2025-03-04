---
header:
    image: /assets/images/hd_test_spring_state_machine.png
title:  user_regexp_in_azure_waf_firewall_custom_rules
date: 2025-03-04
tags:
    - tech
permalink: /blogs/tech/en/use_regexp_in_azure_waf_firewall_custom_rules
layout: single
category: tech
---
> Strength does not come from physical capacity. It comes from an indomitable will. - Mahatma Gandhi

# Mastering Regex in Azure WAF: Unlocking the Power of Custom Rules

## Introduction: The Regex Awakening

Let's be real—writing **regular expressions** can feel like casting dark magic. You stare at cryptic symbols, hoping your spell (uh, regex) works without turning your WAF policy into an instant **"Block Everything"** mode. 🛑

But fear not! Today, we're diving deep into **Azure Web Application Firewall (WAF) custom rules** with regex to unlock their full potential.

By the end of this guide, you'll not only **master regex for Azure WAF**, but also feel confident enough to **bookmark this page** because—trust me—you’ll want to come back to it! 😉

---

## The Challenge: URLs, Query Parameters & The WAF Blocker Beast

Imagine you have a WAF rule that allows traffic only if the `Referer` header matches a specific pattern.

Firslty here is what look like in Azure WAF config page

![img1](/assets/images/2025-03-04-image.png)

You want to allow requests coming from:

- `https://myapp.example.com/dashboard`
- `https://myapp.example.com/app`
- Any **subdirectories** under those paths, such as:
  - `https://myapp.example.com/dashboard/admin`
  - `https://myapp.example.com/app/home`
  - `https://myapp.example.com/dashboard/reports/custom`

Sounds simple, right? But there's a catch: **some URLs have query parameters** (`?` and `=`).

For example:

✅ **Valid request:**
```
https://myapp.example.com/app/customPortal?PortalType=Dashboard&user=admin
```
🚨 **Old regex fails for this!**

---

## The Broken Regex (And Why It Fails)

Initially, you might write something like this:

```regex
^https:\/\/myapp\.example\.com\/(dashboard|app)(\/.*)?$
```

Looks good, right? Wrong. 😬 This regex works **only** for URLs **without query parameters**.

**Why?**
- The regex **stops matching after the last `/`**.
- It does **not** account for `?`, `=` and everything after.

For example:

| URL | Matches? |
|----|----|
| `https://myapp.example.com/app/home` | ✅ Yes |
| `https://myapp.example.com/app/home?user=admin` | ❌ No |
| `https://myapp.example.com/dashboard/reports?sort=asc&page=2` | ❌ No |

---

## The Fix: A Regex That Handles Everything!

To support **query parameters**, we modify the regex:

```regex
^https:\/\/myapp\.example\.com\/(dashboard|app)(\/.*)?(\?.*)?$
```

**New Additions:**
- `\?.*` → This matches **everything after the `?`**, including `=` and `&`.
- `(\?.*)?` → The `?` at the end makes the whole thing **optional**, so URLs **without query parameters still match**.

### **Now, it works for all cases!** 🎉

| URL | Matches? |
|----|----|
| `https://myapp.example.com/app/home` | ✅ Yes |
| `https://myapp.example.com/app/home?user=admin` | ✅ Yes |
| `https://myapp.example.com/dashboard/reports?sort=asc&page=2` | ✅ Yes |

---

## Conclusion: Regex Superpowers Unlocked! 🦸‍♂️

With this regex, you can now confidently write **Azure WAF custom rules** that:

✅ Allow **nested subfolders** under specific paths.
✅ Support **query parameters** (`?`, `=`, `&`).
✅ Prevent unintentional blocks and late-night debugging nightmares. 😅

Now go forth, **write regex like a pro**, and **share this guide with your fellow devs**—they’ll thank you later! 🚀

**Bonus Tip:** Bookmark this page so you can flex your regex skills the next time someone struggles with WAF rules. 😉

---

Need more help? Drop a comment below and let’s decode regex together! 🧩

