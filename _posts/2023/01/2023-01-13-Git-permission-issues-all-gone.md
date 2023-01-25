---
header:
    image: /assets/images/hd_magic_micronaut_jpa.jpg
title:  One killer page to fix most permission issues when using Git
date: 2023-01-13
tags:
 - Git
 
permalink: /blogs/tech/en/Git_permission_issues_all_gone
layout: single
category: tech
---

> The best way to predict the future is to create it.

# Git push failure on error
## Symptoms
```shell
ERROR: Permission to CloudsDocker/cloudsdocker.github.io.git denied to your_user_id.
fatal: Could not read from remote repository.
Please make sure you have the correct access rights
and the repository exists.

```
## Solutions
This is because your PSK key are not loaded, you can firslty check

```shell
ssh-add -L
```
If there are something wrong, you can try to start with fresh, to clean all keys and then add your desired key
```shell
ssh-add -D
ssh-add ~/.ssh/id_rsa_your_key_name
```


--HTH--



