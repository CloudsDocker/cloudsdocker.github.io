---
header:
    image: /assets/images/know-git-symbolic-ref-as-guru.jpg
title:  Not just use git but know how git symbolic-ref work
date: 2023-02-15
tags:
 - Git
 
permalink: /blogs/tech/en/know-git-as-guru
layout: single
category: tech
---

> Superheros come in all shapes and sizes.

# Know details of how git work
You use git very frequently, right? maybe many times each week or each day. But do you really know what's the actual logic once you punched a git command in command line window? Thinking to be a guru everybody admires? let's read more of this short article.

## symbolic-ref

Firstly let's take a look at below command and guess what's it for?

```sh
git symbolic-ref --short -q HEAD
```
Answer time:
* it will return the branch name you are currently working on, e.g. if you are on a feature branch 'hot-fix-123', it will give you `hot-fix-123`


git symbolic-ref is a command in the Git version control system that is used to create, modify, or read symbolic references. A symbolic reference, also known as a "symbolic link," is a type of reference that points to another reference, rather than directly to a commit.

Checkout below sample screenshot FYI:

![](/assets/images/know-git-symbolic-ref-as-guru-1.png)

and this one for ref

![](/assets/images/know-git-symbolic-ref-as-guru-2.png)


When you use git symbolic-ref, you can create or modify a symbolic reference to point to a specific branch or tag in your Git repository. This can be useful when you want to update the target of a reference without changing the reference itself, or when you want to create a temporary reference to a particular commit.

The syntax of the git symbolic-ref command is as follows:
```shell
git symbolic-ref [options] <name> [<ref>]

```

Here, <name> is the name of the reference you want to create or modify, and <ref> is the target of the reference. If you don't specify <ref>, git symbolic-ref will display the current target of the reference.

Some common options for git symbolic-ref include -d to delete a symbolic reference, -q to suppress output, and -m to change the message associated with a reference.

Note that git symbolic-ref is just one of many commands available in Git, and it is typically used in conjunction with other Git commands to manage and track changes in your codebase.




It actually reads which branch head the given symbolic ref refers to and outputs its path, relative to the .git/ directory. 
Typically, you would give HEAD as the <name> argument to see which branch your working tree is on.

A symbolic ref is a regular file that stores a string that begins with ref: refs/. 
For example, your .git/HEAD is a regular file whose contents are ref: refs/heads/master.

Moreover, if you give `--delete` and an additional argument, deletes the given symbolic ref.



--HTH--



