---
header:
    image: /assets/images/git_bible.png
title: GIT useful scripts or error solutions
tags:
- DevOps
date: 2022-04-08 06:40:12
permalink: /blogs/tech/en/most_frequent_git_commands
layout: single
category: tech
---
> Don’t wish for it, work for it.

# Git errors

## auto completion when you press tab key try to complete branch name

This is when you type `tab` key after enter some keyword , e.g. TK-12, which you expect the full branch name e.g. `TK-1234-fix` to be filled in command line automatically.

### Solution
This is because your don't install or something wrong to the `bash-completion`, just run 
```bash
brew install bash-completion
```

## remote: Repository not found.
```bash
git pull
remote: Repository not found.
fatal: repository 'https://github.com/xxxxx.git/' not found
```
### Solution
 - (1) This is indicate you have no network access to it. It most likely you are running the command behind of corporation firewall. So to check and set two environment variable `HTTP_PROXY` and `HTTPS_PROXY`.
 - (2) Another reason would be your password or authentication expired, trying to create new token and add to your github account: take a look at : https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account

## Checkout remote branch and keep track 
```bash
git checkout --track origin/bugfix/fix-branch
```


# Script bible

## Mac Shells
To show what shell you are using. 
```bash
echo $0
chsh -s /bin/bash
chsh -s /bin/zsh
```

## ZSH
To list current shell
```
ps -p $$
```

## brew command not found issues
You are pretty sure homebrew is installed but can't find this command when you run `brew` somewhere.

### troubleshooting
This is generally lated to different shell installed, such as `zsh` or `oh-my-zsh` in M1 chipset MacBook. 

### Solution
Firstly change your shell to zsh 

```bash
chsh -s /bin/zsh
```

Secondly, open the file ~/.zshrc and add following line at end of the file 
```
eval $(/opt/homebrew/bin/brew shellenv)
```

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

## to show files committed but not pushed
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
