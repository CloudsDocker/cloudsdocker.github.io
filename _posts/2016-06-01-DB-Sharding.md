---
layout: posts
title: Database sharding
tags:
 - DB
 - Sharding
 - MobileInternet
---

# DB sharding in YHD

There are two solutions when DB becoming bottleneck in yihaodian. 

- Scale up
Upgrade Oracle DB, adding more CPU , Disk and memory to incrase I/O performance. This is for short term only, high cost.
- Scale out
Divide the order table to multiple DBs, which is support horizontal extension, for long term purpose.


Orgional Oracle is replaced by multiple MySQL DB, supporintg one master and multiple slaves, supporitng segratation of read and write. Leveraging `MySQL built-in` Master-slave replication (SLA<1 second)

## sharding dimensions
- DB Field chosing, it should chose the filed that lead to least SQL and code change, to make the access fall in `one database`, instead of multiple DBs, which result in high I/O and significant logic change. 
- Here is one practice
-- Get all SQL
-- Pick up top fields appear in `where` clause.
-- List break down from three categories
1. Single ID, i.e. userID=?
1. Multiple ID. i.e. userID in (?,?,?)
1. Not show

|Field| Single ID | Multiple ID | Not show|
|:---| ---:| ---:| ---:|
|userID | 120 | 40| 330|
|orderID | 60 | 80| 360|
|shopID | 15 | 0| 485|
It's obviously we should chose userID for sharding. Hold on, this is just **static** analysis, we should conduct *dynamic** study as well, so list most executed SQLs, e.g. top 15 SQL (account to 85% of SQL calls), if we conduct sharding by user ID, 85% of those SQL will fall in single DB and 13% fall in multiple DB, and only 2% will scan all DB, so the performance is must better than sharding on other ID fields.


## sharding strategy

There are two type of strategies
1. By value range, e.g. user ID 1-9999 to DB1, and 10000-20000 to DB2. For this option, 
1. By value mod, e.g. userID mod n, when reminder is 0, go to DB1, reminder is 1, to DB2, etc.

Pros and Cons:

|Criteria| By Range| By Mod | 
|:---|:---|:---|
|number of DBs |initially only require small amount of DBs, can increasse by business requests | initially number based on mod number, normally a big number|
|Accessibility|initially only few DBs, perforamce cost is small, single DB performance query is poor|initially big number of DBs, query acorss DBs may consume many resources, better for query on single DB|
|DBs adjustment|easy, just add new DB, and impact is limit when split existing DB |not easy, change mod value  may result in DB migration across DBs|
|Data hotspot|there are data hotspot issues|no data hotspot issues|

In practice, for the sake of simplicity, mod sharding is often used. To manage further sharding, and for smooth data migration, normally new DBs are added by folds, e.g. intially 4 DBs, furhter split will be 8 DBs, then 16 DBs. This is becuase only half of data in existing DB will be migrated to new DB, while the rest half will be remain unchanged. However, there are some super IDs, e.g. one big shop with massive records than normal, if we shard DB by user ID, there will one DB will many records than others. For this case, we need to provide separate DB for those super IDs.

## sharding numbers
Firslty, that's depends on the ability of single DB, e.g. normally one MySQL DB can support upto 50mio records, and Oracle can support 100mio. Normally multiple DBs may leads to certain perforamnce issues, when data query across multiple DBs, if there are multithreading call, it will cost precious thread resource, while it's single thread, the wating time will be unacceptable. Normally, the initial sharding is 4-8 DBs.

## Router transparency
To certain extent, DB sharding means change of DBSChema, which inevitable result in application, however, this is irrelavent to business logic, so the DB sharding should be transparent to business logic code, therefore, DB sharding should be handled at DAL (Data Access Layer) or DDAL (Distributed Data Access Layer).

1. For access to single DB, e.g. query by certain user id, DAL will automatically route to that DB, even further split by mod, still no applicaiton logic code change impacted.
1. For simple across DB query, DAL in charge to aggregate results from every DB query, still transparent to upper application logic.
1. For query involves multiple DBs with aggretation functions, e.g. groupBy, order by, min, max, avg. It's recommended DAL consolidate request from single DB, while upper layers do further processing. That's becuase if rely on DAL, it would be too complex, and such case is relatively rare case, so leave it to upper layer.


# Oracle Sharding
It's required in Web 2.0 and high availability technologies

Shardingis an application-managed scaling technique using many (hundreds /thousands of) independent databases 
- Data is split into multiple databases (shards)
- Each database holds a subset (either range or hash) of the data
- Split the shards as data volume or access grows
- Shards are replicated for availability and scalability

Sharding is the dominant approach for scaling massive websites

- Application code dispatches request to a specific database based on key value
- Queries are constrained -simple queries on shard-key
- Data isdenormalizedto avoid cross-shard operations (no joins)
- Each database holds all the data
- Request dispatched to a specific database based on read/write,key value
- Updates go to one database, changes are replicated to the other databases. The other databases are available for reads
- Provides read scalability
- Can be combined with horizontal sharding so that each shard is replicated to a different degree
- Main benefit is that you do not need to reshard


## Downsides of DB replica

- Only async log shipping which can lose data in case of failure
- Slaves can return inconsistent data
- Statement based replication has correctness issues & row-based replication is immature
- Replication is slow (high overhead on each reader, slaves are single-threaded)
- No support for failover between master (primary) & slaves (backup)
- Does not handle failure conditions such as missing or damaged logs
- Storage engine and replication state may become inconsistent after a crash
- Bringing a failed master back requires copying the database


--End--
