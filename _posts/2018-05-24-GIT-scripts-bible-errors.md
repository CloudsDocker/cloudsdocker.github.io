---
title: GIT useful scripts or error solutions
tags:
- DevOps
date: 2007-04-28 06:40:12
layout: posts
---

# Script bible

## to list merge conflicts files in command line
You can use either one of below three commands
```bash
git diff --name-only --diff-filter=U
git status --short | grep "^UU "
git ls-files -u
```

## One line command to add, commit and push one changed file
```bash
git status --short | awk '{split($0, a);print a[2]}' | xargs git add && git commit -m 'commit changes' && git push origin BRANCH_NAME
```

## to show files commited but not pushed
```bash
git diff --stat --cached origin/feature/BRANCH_NAME
```

## to view file content changed
```bash
git show PATH/abc.sql
```

## show file change logs

`git log` is the powerful command for this kind of tasks, as below sample commands
```bash
git log --pretty=format:"%h [%an] %s" --graph

git log --pretty=format:"%h [%an] %s" --graph --since=7.days
```
* %h means short hash
* %s is subject

```bash
git log --pretty=format:"%h [%an] %s" --graph --since=7.days -S bower.json 
git log --pretty=format:"%h [%an] %s" --graph --since=7.days --grep Npm
git log --pretty=format:"%h [%an] %s" --graph --since=7.days --committer todd
```
* -S keyword_of_filter_files

## Get `correct` branch name

Sometimes, if you checkout new branch with incorrect case. It still can check it out to local but you'll get errors when you try to push it to remote.

To solve this issue, please use following command to get `correct` branch to checkout
```bash
git fetch && git for-each-ref | grep -i 'THE KEY WORD'  | awk '{split($0,a);print a[3]}'
git checkout -b BRANCH_NAME_FROM_ABOVE
```

# Errors


## failed to push change
Errors as below
```bash
fatal: unable to access 'https://tzhang@stash.xxx.com/scm/abc.git/': SSL certificate prob
lem: self signed certificate in certificate chain
```
### Solutions:

```bash
git config --global http.sslVerify false
```
