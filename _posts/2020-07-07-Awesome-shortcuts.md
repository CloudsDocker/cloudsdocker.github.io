---
header:
    image: /assets/images/hd_shortcuts.png
date: 2022-04-16
title: Awesome Shortcuts to boost productivities
permalink: /blogs/tech/en/core_java_for_interview
layout: single
category: tech
---

# Shortcuts & tips
## zoom
 - Cmd+Shift+A: mute
 - CMd+W: leave meeting.
 - Fn+F: toggle full screen

## Microsoft TEAMS

> Replace `Cmd` with `Ctrl` for **Windows** platform
Cmd +Shift+M: mute
Cmd +Shift+H: leave meeting
Cmd + . : to show list of all shortcuts
Cmd + / : to focus in search bar
Cmd + G: go to find a person to start talk 
Cmd + F: Open filter
Cmd + +: to zoom in to show bigger font
Cmd + -: to zoom out to show smaller font
Cmd + 0: to zoom in to show original font

Cmd + 2: Go to Chat
Cmd + 3: Go to Teams group

Options + Up/Down: move to previous/next item in left pane, e.g. Cmd+2, then Alt+Down to move to next conversation in left conversation pane.


## Microsoft VS Code:
- Ctrl+0 : go to first pane, e.g. if file explorer opened, this will put focus on files explorer
- Ctrl+Shift+E: toggle focus onto files explorer, first press "Ctrl+Shift+E" will focus files explorer, second press "Ctrl+Shift+E" will focus file editor pane
- Ctrl+e: open recently files
- F1: to show command platte, same as "Ctrl+Shift+P"

### VSCode plugins
- All Autocomplete: for english typing auto complete

## Intellij Notes

### Windows

 - `Ctrl+Alft+F12` : Open current file in `Explorer`, you can chose which level to show, e.g. this file, it's parent, grand parent etc.
 - CMD+3: Open actions (Eclipse)
 - CMD+F12 (Mac) or Option+F12: Show terminal
- Shift+ESC: close auxiliary windows, such as project explorer, terminal window, etc.
- Cmd+O: File structure, list all methods
- Shift+Cmd+F: reformat code

## Sublime

- [ ]  Ctrl+-:  Go to last edit:

## Notion Notes

Cmd+\: show left bar

Cmd+P: global search

# Mac tips
 * Cmd + ← or → : move cursor to begin or end of line
 * Shift + Cmd + →: select whole line (move cursor to line front first)
 * Option + Shift + → / ←: select whole word
 * ^ + Down: to show various `instance window` of current application, e.g. show different window of Chrome windows, you can use `Ctrl+\`` to switch in different instance window. 
 * Ctrl+F2: to access menu bar

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
