---
title: Day-Day-Up-Java
date: 2021-10-11
tags:
 - Java
 - Tips
layout: single
category: tech
---


# More developer friendly Threa Sleep

Besides calling Thread.sleep(30000) indicate sleep 30 seconds, but is it too confusing to count how many zeros there? 
Alternatively you can use `TimeUnit` To increase readability, I believe you'll gree following one is easier to understand for non obvious durations :
```java
TimeUnit.SECONDS.sleep(30); // sleep 30 seconds
```












 

--End--
