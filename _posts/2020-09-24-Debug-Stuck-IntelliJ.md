---
title: Debug Stuck IntelliJ
date: 2020-09-24
tags:
 - IntelliJ
 - Java

layout: post
---

# What?
Sometimes when you try to debug a class in Intellij but it stuck there and never proceed, e.g. the status is `Instantiating tests ...` and never returns

# How to fix

## Firstly disable ALL breakpoints
It maybe too many breakpoints in your project, so go to menu `run` -> `View breakponts` to **Untick** ALL breakpoints. Rather than `mute all breakpoints` in Debugger view.

## Change Intelij to use JUnit to run test
Different Intellij veions has different approach to run a test or debug. My case is Intellij try to debug a class by `gradle` runner, which cause debug stuck. When I try to switch it to `JUnit` runner, all working fine. 

Here are steps to switch to Junit

 - Go to menu `Run` -> `Edit Configurations`, then click "-" to remove your test configuration
 - Go to IntelliJ preference, search "Gradle", then change value in two drop down to "IntelliJ" , rather than `Gradle(default)`


--End--
