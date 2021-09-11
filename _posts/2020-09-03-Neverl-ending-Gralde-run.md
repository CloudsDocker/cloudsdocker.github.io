---
title: Gradle build stuck
date: 2020-09-03
tags:
 - Gradle
 - Java
layout: posts
---

# Gradle build stuck, keep on running but never ending

Here are some key error in console logs

- Waiting to acquire shared lock on daemon addresses registry
- Daemon stuck
- Gradle build stuck at “Waiting to acquire shared lock on daemon addresses registry.”

## Here are sample logs from Gradle console

```bash

22:18:32.549 [DEBUG] [org.gradle.cache.internal.DefaultFileLockManager] Waiting to acquire shared lock on daemon addresses registry.
22:18:32.549 [DEBUG] [org.gradle.cache.internal.DefaultFileLockManager] Lock acquired on daemon addresses registry.
22:18:32.549 [DEBUG] [org.gradle.cache.internal.DefaultFileLockManager] Releasing lock on daemon addresses registry.
22:18:32.550 [DEBUG] [org.gradle.cache.internal.DefaultFileLockManager] Waiting to acquire shared lock on daemon addresses registry.
22:18:32.550 [DEBUG] [org.gradle.cache.internal.DefaultFileLockManager] Lock acquired on daemon addresses registry.
22:18:32.550 [DEBUG] [org.gradle.cache.internal.DefaultFileLockManager] Releasing lock on daemon addresses registry.
22:18:33.386 [DEBUG] [org.gradle.process.internal.health.memory.MemoryManager] Emitting OS memory status event {Total: 34359738368, Free: 14353453056}
22:18:33.386 [DEBUG] [org.gradle.launcher.daemon.server.health.LowMemoryDaemonExpirationStrategy] Received memory status update: {Total: 34359738368, Free: 14353453056}
22:18:33.386 [DEBUG] [org.gradle.process.internal.health.memory.MemoryManager] Emitting JVM memory status event {Maximum: 1908932608, Committed: 1227358208}
```
## Investigation

### List process
To see what happending behind the scene, firstly run `jps` and get process IDs for **Gradle** , e.g. output as

```bash
~|⇒  jps
8304 
72803 KotlinCompileDaemon
72501 GradleDaemon
73700 GradleDaemon
74823 GradleWrapperMain
75366 Jps
74603 KotlinCompileDaemon
636 
71455 GradleDaemon
74846 ApplicationKt
```

### Show details of Gradle Daemon 

To know more about stack trace for Gralde, use following command
```bash
jstack 72501
```
There are lots of waiting process, which indicate they are waiting for further signal to go ahead.

# Solution
Then it turn out there is gradle argument debug in grade command list beow:

`./gradlew bootRun --debug-jvm --stacktrace`

So you should **open debug** to attach the process. i.e. go to **Run** and click **Attach to process** and select your assigned point, then Gradle process would resume and continue to run.

--end--
