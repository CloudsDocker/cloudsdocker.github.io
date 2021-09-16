---
title: How to get CPU name, core, 64bit and speed in command line
date: 2021-09-14
tags:
 - Windnows
 - WMI
layout: single
---

# Summary
In windows operation system, if you want to get your CPU name, core, 64bit and speed in command line. Just follow below actions:

   1. Press `Win+R` and type *cmd*
   1. Enter following command to get your CPU details.

```bash
wmic cpu get caption, deviceid,name, numberofcores,maxclockspeed,status
```
You'll get output simliar to below:

![](/assets/images/ShowCPUsInWin.png)

```bash
Caption                               DeviceID  MaxClockSpeed  Name                                NumberOfCores  Status

Intel64 Family 6 Model 85 Stepping 7  CPU0      3912           Intel(R) Xeon(R) W-2245 CPU @ 3.90GHz  8              OK
```

Addtionally reading, this `wmic` is an utility shipped by Windows OS. It's full name is WMI command-line (WMIC) , one utility provides a command-line interface for Windows Management Instrumentation (WMI).


--End--
