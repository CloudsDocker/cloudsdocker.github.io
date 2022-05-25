---
header:
    image: /assets/images/hd_sdkman_omz.png
title:  Error in WSL in windows, command not found: sdk 
date: 2022-05-18
tags:
 - wsl
 - dev
 - windows
 - zsh
 - omz 
permalink: /blogs/tech/en/command-not-found-sdk-in-omz-zsh-wsl-windows
layout: single
category: tech
---

> Never stop learning, because life never stops teaching.

# Summary
Within omz (oh-my-zsh) or zsh in the WSL runtime of Windows, sometimes you've installed sdkman in one terminal. The sdk worked fien, however when you open a new terminal and try to run sdk command, you'll get following error:

```bash
sdk vesrion

zsh: command not found: sdk
```

# Error details & solutions

The root cause is the 1st installation failed to setup sdk init variables into system envrionment. This is related to special requirement in `omz` .

omz using following structure to save your personal environment varaibles, i.e. 

```
~/.oh-my-zsh/custom/example.zsh
```
In short, omz will scan and find any *user customized variables* under folder **custom**. 
So you can add your own file , e.g. `obama.zsh` or update the default `example.zsh`.

So you'd add following line into above file.

```bash
source "/home/YOUR_USER_NAME/.sdkman/bin/sdkman-init.sh"

```

Then run 
```bash
sdk vesrion
```
You'll find your favorate sdk back to working now.



# Similar error
After installation of `omz` you'll find some settings may stop working as well, such as following errors:

 -  Could not connect to security.ubuntu.com:80 on "sudo apt update"
 - github.com cann't connected or fatal error

This is similar to above reason. If you are running behind corporation firewall, your HTTPS proxy were setup for *bash* but now you need to add it to *omz* and `zhs`. Here are some samples:

```bash
export http_proxy=http://abc.testcorp.com:8080
export https_proxy=http://abc.testcorp.com:8080
export HTTP_PROXY=http://abc.testcorp.com:8080
export HTTPS_PROXY=http://abc.testcorp.com:8080
export GIT_SSL_NO_VERIFY=1
export NO_PROXY=localhost,nexus.abc.testcorp.com
```





--HTH--



