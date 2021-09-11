---
Layout: page
title: Github page commands notes
tags:
 - Git
 - GitPages
layout: posts
---

# 404 error for customized domain (such as godday)
```sh
404
There is not a GitHub Pages site here.
```
- Go to github master branch for gitpages site, manually add CNAME file

## following lages are searchable in google 

- [alice](http://byalice.github.io/2016/06/04/Build-Blog/)
- gihub

# Travis errors:

 Got following errors in Travis page:

## branch not included or excluded

`solution`: that's because your source branch, such as 'blogSrc' should be added in whitelist of .travis.yml, for instance

```sh
branches:
  only:
  - blogSrc
```

## fatal: empty ident name
Because *--global* is requried when setting up travis , below is the sample
```sh
git config --global user.email abc@def.com
```
