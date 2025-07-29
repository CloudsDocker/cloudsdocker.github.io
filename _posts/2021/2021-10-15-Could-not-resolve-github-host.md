---
title: Failed to talk to github.com from corporation network
date: 2021-10-11
tags:
 - KsqlDB
 - Kafka
layout: single
category: tech
---


# Background
It's typical to get various network connection issues when you run commands within corporation network. For example, you'll find diversed issues when you trying to fetch/push about your repository host in github.com.

here is a short-and-sweet page to illustrate on how to sort it out by yourself.

# Errors

## Could not resolve host: github.com

### Symptom 
```bash
git push
fatal: unable to access 'https://github.com/your_repo/repo1.git/': Could not resolve host: github.com
```
This is emblematic `network proxy` error. 

### Solution
Depends on your running command line tool (e.g. windows prompt, gitbash, cmder, etc.) you can run following command prior to your git command
```bash
export http_proxy=http://your-company-proxy.com:8080/;
```
or 

```bash
set http_proxy=http://your-company-proxy.com:8080/;
```





## Authentication failed for: https://github.com/your_repo
### Symptom
```bash
git push
remote: Invalid username or password.
fatal: Authentication failed for 'https://github.com/your_repo/repo1.git/'
```

### Solution
#### Summary
This is related to your personal API token. So got to https://github.com/settings/tokens check your token status, whether it's expired. 

![](/assets/images/github_proxy.png)


- If it's expried, go to genearate a new one via https://github.com/settings/tokens/new 

> If this is for your personal usage, you can chose "No expiration" in dropdown in new token page.

- Copy your newly geneated personal access token, then rerun your command in command console
- You'll get a pop up window to ask for your new token. Paste it here as below screenshot

![](/assets/images/github_input_token.png)

 - Check running status in your command console, it shoud working fine now.
 - Grab a coffee and enjoy it. :coffee: :joy:

# Reference
 - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

--End--
