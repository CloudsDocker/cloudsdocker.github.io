---
title: Awesome Shortcuts
date: 2020-07-07
layout: posts
---

# Shortcuts & tips

# Intellij Notes

- CMD+3: Open actions (Eclipse)
- CMD+F12 (Mac) or Option+F12: Show terminal
- Shift+ESC: close auxiliary windows, such as project explorer, terminal window, etc.
- Cmd+O: File structure, list all methods
- Shift+Cmd+F: reformat code

# Sublime

- [ ]  Ctrl+-:  Go to last edit:

# Notion Notes

Cmd+\: show left bar

Cmd+P: global search

# Mac tips

- [ ]  Cmd + ← or → : move cursor to begin or end of line
- [ ]  Shift + Cmd + →: select whole line (move cursor to line front first)
- [ ]  Option + Shift + → / ←: select whole word
- [ ]  ^ + Down: to show notiifcation center
- [ ]  Ctrl+F2: to access menu bar

# Linux comands

- List only folders:

ls -dl conflu*

sudo lsof -i tcp:3000

lsof is a command line utility for all Unix and Linux like operating systems to check “list of open files”

- Redirect

using `> /dev/null 2>&1` will redirect all your command output (both `stdout` and `stderr`) to `/dev/null`, meaning no outputs are printed to the terminal.

By default:

```
stdin  ==> fd 0
stdout ==> fd 1
stderr ==> fd 2

```

In the script, you use `> /dev/null` causing:

```
stdin  ==> fd 0
stdout ==> /dev/null
stderr ==> fd 2

```

And then `2>&1` causing:

```
stdin  ==> fd 0
stdout ==> /dev/null
stderr ==> stdout
```

# Docker

## commands

- docker network ls

list all docker networkds

- docker rmi:

remove and un-tags one or more images from the host node

# Junit

No tests found for given includes: [

import org.junit.Test rather than import org.junit.jupiter.api.Test

# Kotlin

## Errors

lateinit property sut has not been initialized
kotlin.UninitializedPropertyAccessException: lateinit property sut has not been initialized
