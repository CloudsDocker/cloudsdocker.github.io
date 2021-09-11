---
layout: posts
title: Setup Git in Mint Linux 
tags: 
 - Git
 - Mint
---

# How to setup Git in Mint Linux
=================================================

- git config --global user.name "Todd Zhang"
- git config --global user.email phray.zhang@gmail.com
- git config --list
- git clone https://github.com/todzhanglei/todzhanglei.github.io 
- git config --global credential.helper cache
- git config --global credential.helper 'cache --timeout=36000'

## To add remote
```sh
git remote add origin https://github.com/CloudsDocker/cloudsdocker.github.io.git
```
Above command will add the remote URL with alias "origin"

## To pull specific branch
```sh
git pull origin blogSrc
```

# Errors

## Error: The following untracked working tree files would be overwritten by checkout

```sh
git clean  -d  -fx ""
```


