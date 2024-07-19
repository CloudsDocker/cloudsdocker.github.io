---
title: Notes and pitfalls for redis development
header:
    image: /assets/images/refind-java-SOLID-principles.jpg
date: 2024-01-06
tags:
- Networking
- TraceRoute
- Network Diagnostics

permalink: /blogs/tech/en/Redis-dev-notes
layout: single
category: tech
---
> A younger brother knows his older brother better than anyone else.

# Unlocking Network Secrets: A MacBook Traceroute Tutorial

## Errors Pool not open

```
redis.clients.jedis.exceptions.JedisConnectionException: Could not get a resource from the pool
	at redis.clients.jedis.util.Pool.getResource(Pool.java:59) ~[jedis-3.3.0.jar:na]
	at redis.clients.jedis.JedisPool.getResource(JedisPool.java:288) ~[jedis-3.3.0.jar:na]
	at com.thinkchina.unifyxp2.events.sub.RedisQueueEventSubscriber.doSubscribe(RedisQueueEventSubscriber.java:37) ~[classes/:na]
	at java.base/java.util.concurrent.CompletableFuture$AsyncRun.run(CompletableFuture.java:1736) ~[na:na]
	at java.base/java.util.concurrent.CompletableFuture$AsyncRun.exec(CompletableFuture.java:1728) ~[na:na]
	at java.base/java.util.concurrent.ForkJoinTask.doExec(ForkJoinTask.java:290) ~[na:na]
	at java.base/java.util.concurrent.ForkJoinPool$WorkQueue.topLevelExec(ForkJoinPool.java:1020) ~[na:na]
	at java.base/java.util.concurrent.ForkJoinPool.scan(ForkJoinPool.java:1656) ~[na:na]
	at java.base/java.util.concurrent.ForkJoinPool.runWorker(ForkJoinPool.java:1594) ~[na:na]
	at java.base/java.util.concurrent.ForkJoinWorkerThread.run(ForkJoinWorkerThread.java:183) ~[na:na]
Caused by: java.lang.IllegalStateException: Pool not open
	at org.apache.commons.pool2.impl.BaseGenericObjectPool.assertOpen(BaseGenericObjectPool.java:440) ~[commons-pool2-2.11.1.jar:2.11.1]
	at org.apache.commons.pool2.impl.GenericObjectPool.borrowObject(GenericObjectPool.java:277) ~[commons-pool2-2.11.1.jar:2.11.1]
	at org.apache.commons.pool2.impl.GenericObjectPool.borrowObject(GenericObjectPool.java:223) ~[commons-pool2-2.11.1.jar:2.11.1]
	at redis.clients.jedis.util.Pool.getResource(Pool.java:50) ~[jedis-3.3.0.jar:na]
```
### Solution
This is because of wrong jedis method used, the data in redis is hashmap but was trying to get data from list.
--HTH--