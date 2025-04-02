---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  Git Behind the Firewall: - Fix Connection Reset by Port 22 Errors in Corporate Networks"
date: 2025-04-02
tags:
    - tech
    - DevOps
    - Enterprise Security
    - GitHub
    - SAML SSO 
permalink: /blogs/tech/en/git-connection-reset-within-corporation-network
layout: single
category: tech
---
> Happiness is not something ready made. It comes from your own actions. - Dalai Lama

# Fixing "Connection Reset by Port 22" Errors in Corporate Git Environments

Are you struggling with SSH-based Git connections failing within your company network? That dreaded "Connection reset by port 22" error message can stop your workflow dead in its tracks. In this comprehensive guide, I'll walk you through why this happens and provide a bulletproof solution using Personal Access Tokens (PATs) that will get you back to coding in minutes.

## The Problem: SSH Connections Blocked by Corporate Firewalls

```
Connection reset by 4.237.22.38 port 22
fatal: Could not read from remote repository.
Please make sure you have the correct access rights
```

This error typically occurs because many corporate networks block SSH connections (port 22) for security reasons. Your Git remote is configured to use SSH, but your company's firewall is preventing the connection from being established.

## Why This Happens

Corporate firewalls often block SSH connections (port 22) for several legitimate security reasons:

1. **Security Policies**: Many organizations restrict outbound SSH to prevent data exfiltration
2. **Network Segmentation**: Internal development environments may be isolated from external services
3. **Traffic Monitoring**: HTTPS traffic (port 443) can be more easily monitored than SSH
4. **Compliance Requirements**: Regulatory standards may require certain types of connections

## The Solution: Switch from SSH to HTTPS with a Personal Access Token

The most reliable workaround is to switch your Git remote from SSH to HTTPS and authenticate using a Personal Access Token (PAT). Here's a step-by-step guide:

### 1. Generate a Personal Access Token on GitHub

1. Go to your GitHub account settings (click your profile picture → Settings)
2. Select "Developer settings" from the left sidebar
3. Click on "Personal access tokens" → "Tokens (classic)"
4. Click "Generate new token" → "Generate new token (classic)"
5. Give your token a descriptive name (e.g., "Work Computer Git Access")
6. Under "Select scopes," check the "repo" box to grant full control of private repositories
7. Click "Generate token"
8. **IMPORTANT**: Copy your token immediately and store it securely (e.g., in a password manager). GitHub will only show it once!

### 2. Change Your Remote URL from SSH to HTTPS

First, check your current remote configuration:

```bash
git remote -v
```

You'll likely see something like:
```
origin  git@github.com:username/repository.git (fetch)
origin  git@github.com:username/repository.git (push)
```

Now, change the remote URL from SSH to HTTPS:

```bash
git remote set-url origin https://github.com/username/repository.git
```

Replace `username/repository.git` with your actual GitHub username and repository name.

### 3. Pull from Your Repository

Now try pulling from your repository:

```bash
git pull
```

Git will prompt you for authentication:
- For username: Enter your GitHub username
- For password: Paste your Personal Access Token (not your GitHub password)

### 4. Store Your Credentials (Optional but Recommended)

To avoid entering your credentials repeatedly, you can configure Git to store them:

```bash
git config --global credential.helper store
```

**Note**: This stores your credentials in plaintext on your local machine. If you're on a shared computer, consider using the cache helper instead:

```bash
git config --global credential.helper 'cache --timeout=3600'
```

This will cache your credentials for 1 hour (3600 seconds).

## Troubleshooting Common Issues

### Still Getting Authentication Errors?

- Make sure your PAT has the correct permissions (at minimum, "repo" scope)
- Verify you're using the token as the password, not your GitHub account password
- Check if your token has expired (GitHub tokens can expire based on your settings)

### Company Blocking HTTPS to GitHub?

In rare cases, companies might also restrict access to GitHub via HTTPS. If this happens:
- Speak with your IT department about allowing connections to GitHub
- Ask if there's an internal Git server or proxy you should be using instead
- Consider requesting a specific exception for development purposes

## Conclusion

Switching from SSH to HTTPS with a Personal Access Token is the most reliable way to access GitHub repositories from within restrictive corporate networks. This approach bypasses the common port 22 blockages while maintaining secure authentication.

By following the steps in this guide, you should be able to resolve the "Connection reset by port 22" error and get back to your development workflow without further interruptions.

Have you encountered other Git connectivity issues in corporate environments? Share your experiences in the comments below!
