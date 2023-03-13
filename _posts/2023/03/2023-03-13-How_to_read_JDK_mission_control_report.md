---
title: How to read JDK mission control report
header:
    image: /assets/images/How_to_read_JDK_mission_control_report.jpg
date: 2023-03-13
tags:
 - Macbook
 - Java
 - PerformanceTuning

permalink: /blogs/tech/en/How_to_read_JDK_mission_control_report
layout: single
category: tech
---
> Live the life you've imagined.

# what "Java Monitor Wait" means

In Java Flight Recorder (JFR), "Java Monitor Wait" is a type of event that indicates a thread is waiting to acquire a monitor lock on an object. When a thread attempts to enter a synchronized block or method on an object, it first attempts to acquire the monitor lock associated with that object. If the lock is currently held by another thread, the current thread will wait until the lock becomes available.

The Java Monitor Wait event in JFR is triggered when a thread is waiting to acquire a monitor lock and has been blocked for a certain amount of time. This event can be useful for identifying synchronization bottlenecks in your application, where threads are contending for the same lock and causing delays. By analyzing the timing and frequency of Java Monitor Wait events, you can identify areas of your code where you can reduce contention and improve performance.

Here is one sample file indicate the actual time out event for a `Java Monitor Wait`:

![](/assets/images/JFR_Monitor.png)


--End--
