---
header:
    image: /assets/images/hd_containers.png
title: Debug Stuck IntelliJ
date: 2020-09-24
tags:
 - IntelliJ
 - Java

layout: posts
---

# What happened to a debug job hanging in IntelliJ (IDEAS) IDE?
You may find when you try to debug a class in Intellij but it stuck there and never proceed, e.g. the status is `Instantiating tests ...` and never returns

# How to fix
There are numeber or reasonse, here are some commonly ones. 

## 1. Too many breakpoints!
Solution is straightforwrd, firstly disable (or delete) ALL breakpoints. Then add only small number of breakpoints to retry.

To do so, please go to menu `run` -> `View breakponts` to **Untick** ALL breakpoints. Rather than `mute all breakpoints` in Debugger view.

Alternatively, you can click menu "hellp" -> "Find Actions..." . Then chose "remove all breakpoitns", As below screenshot.

![](/assets/images/DebugStuckIntelliJ.png)


## 2. Change Intelij to use JUnit to run test
Another possible reason is `how you start a debug test` in your IDE.

Different Intellij veions go with different approach to run a test or debug. 
For my case is Intellij try to debug a class by `gradle` runner, which cause debug hang forever. When I try to switch it to `JUnit` runner, all working fine. 

Here are steps to switch to Junit

 - Go to menu `Run` -> `Edit Configurations`, then click "-" to remove your test configuration
 - Go to IntelliJ preference, search "Gradle", then change value in two drop down to "IntelliJ" , rather than `Gradle(default)`
 


--End--
