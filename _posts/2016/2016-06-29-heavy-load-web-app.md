---
layout: posts
title: heavy load web application
tags:
 - heavy load
 - mobile internet
 - DevOps
---

# Common solutions

With `cache` + `hash`, seems nothing is impossible.

## hash

When involving big data, heavey load and concurrent, the ultimate solution is `hash`, such as random insert, time complexity O(1) etc, the only downside is waste of space, however, storage is cheap recently. `hash` is one must-have for concurrent systems.

## cache

There are many mature cache mechanism, such as KV DB like memcache, redis, and they are supporting clusters, operatibility is good as well.

## read-write segaration
In most cases, there are more read than write operation, so separate database to acccept write request to master DB, and redirect read request to slave DBs. At the same time, multiple salve DBs can be smoothly `scale out`, data replicate can leverage log bin.

## Database separation and sharding
For DB sharding, leverage hash to direct to corresponding DB shard. To ease the load on single host.
