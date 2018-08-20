---
title: Zoo-keeper
---

# ZK Motto
> the motto "ZooKeeper: Because Coordinating Distributed Systems is a Zoo."


# Features of Zookeeper

- Synchronization − Mutual exclusion and co-operation between server processes.
- Ordered Messages - The strict ordering means that sophisticated synchronization primitives can be implemented at the client.
- Reliability - The reliability aspects keep it from being a single point of failure.
- Atomicity − Data transfer either succeeds or fails completely, but no transaction is partial.
- High performant - The performance aspects of Zookeeper means it can be used in large, distributed systems.
- Distributed.
- High avaliablity.
- Fault-tolerant.
- Loose coupling.
- Partial failure.
- High throughput and low latency - data is stored data in memory and on disk as well.
- Replicated.
- Automatic failover: When a Zookeeper dies, the session is automatically migrated over to another Zookeeper.


## Different type of data
When designing an application with ZooKeeper, one ideally separates application data from control or coordination data. For example, the users of a web-mail service are interested in their mailbox content, but not on which server is handling the requests of a particular mailbox. The mailbox content is application data, whereas the mapping of the mailbox to a specific mail server is part of the coordination data (or metadata). A ZooKeeper ensemble manages the latter.


The multiple processes consequently need to implement mutual exclusion. We can actually think of the task of acquiring mastership as the one of acquiring a lock: the process that acquires the mastership lock exercises the role of master.

Coordination does not always take the form of synchronization primitives like leader election or locks. Configuration metadata is often used as a way for a process to convey what others should be doing. For example, in a master-worker system, workers need to know the tasks that have been assigned to them, and this information must be available even if the master crashes.

## How world work without ZooKeeper
It is certainly possible to build distributed systems without using ZooKeeper. ZooKeep‐ er, however, offers developers the possibility of focusing more on application logic rather than on arcane distributed systems concepts. Programming distributed systems without ZooKeeper is possible, but more difficult.

## What does ZooKeeper does not do

The ensemble of ZooKeeper servers manages critical application data related to coor‐ dination. ZooKeeper is not for bulk storage. For bulk storage of application data, there are a number of options available, such as databases and distributed file systems. When designing an application with ZooKeeper, one ideally separates application data from control or coordination data.

ZooKeeper, however, does not implement the tasks for you. It does not elect a master or track live processes for the application out of the box. Instead, it provides the tools for implementing such tasks. The developer decides what coordination tasks to implement.


Processes in a distributed system have two broad options for communication: they can exchange messages directly through a network, or read and write to some shared storage. ZooKeeper uses the shared storage model to let applications implement coordination and synchronization primitives. But shared storage itself requires network communi‐ cation between the processes and the storage. It is important to stress the role of network communication because it is an important source of complications in the design of a distributed system.

This scenario leads to a problem commonly called split-brain: two or more parts of the system make progress independ‐ ently, leading to inconsistent behavior. As part of coming up with a way to cope with master failures, it is critical that we avoid split-brain scenarios.

# Tasks
The following requirements for our master-worker architecture:
Master election
It is critical for progress to have a master available to assign tasks to workers.
Crash detection
The master must be able to detect when workers crash or disconnect.
Group membership management
The master must be able to figure out which workers are available to execute tasks.
Metadata management
The master and the workers must be able to store assignments and execution sta‐ tuses in a reliable manner.

# CAP

known as CAP, which stands for Consistency, Availability, and Partition-tolerance, says that when designing a distributed system we may want all three of those properties, but that no system can handle all three.2 Zoo‐ Keeper has been designed with mostly consistency and availability in mind, although it also provides read-only capability in the presence of network partitions.


# ZooKeeper Basics
Several primitives used for coordination are commonly shared across many applica‐ tions. Consequently, one way of designing a service used for coordination is to come up with a list of primitives, expose calls to create instances of each primitive, and ma‐ nipulate these instances directly. For example, we could say that distributed locks con‐ stitute an important primitive and expose calls to create, acquire, and release locks.
Such a design, however, suffers from a couple of important shortcomings. First, we need to either come up with an exhaustive list of primitives used beforehand, or keep ex‐ tending the API to introduce new primitives. Second, it does not give flexibility to the application using the service to implement primitives in the way that is most suitable for it.
We consequently have taken a different path with ZooKeeper. ZooKeeper does not ex‐ pose primitives directly. Instead, it exposes a file system-like API comprised of a small set of calls that enables applications to implement their own primitives. We typically use recipes to denote these implementations of primitives. Recipes include ZooKeeper operations that manipulate small data nodes, called znodes, that are organized hier‐ archically as a tree, just like in a file system.


## znodes

a few other znodes that could be useful in a master- worker configuration:
- The /workers znode is the parent znode to all znodes representing a worker avail‐ able in the system. Figure 2-1 shows that one worker (foo.com:2181) is available. If a worker becomes unavailable, its znode should be removed from /workers.
- The /tasks znode is the parent of all tasks created and waiting for workers to execute them. Clients of the master-worker application add new znodes as children of /tasks to represent new tasks and wait for znodes representing the status of the task.
- The /assign znode is the parent of all znodes representing an assignment of a task to a worker. When a master assigns a task to a worker, it adds a child znode to /assign.
## API
API Overview
Znodes may or may not contain data. If a znode contains any data, the data is stored as a byte array. The exact format of the byte array is specific to each application, and ZooKeeper does not directly provide support to parse it. Serialization packages such as Protocol Buffers, Thrift, Avro, and MessagePack may be handy for dealing with the format of the data stored in znodes, but sometimes string encodings such as UTF-8 or ASCII suffice.


## The ZooKeeper API exposes the following operations:
```
create /path data
Creates a znode named with /path and containing data
delete /path
Deletes the znode /path
exists /path
Checks whether /path exists
setData /path data
Sets the data of znode /path to data
getData /path
Returns the data in /path
getChildren /path
Returns the list of children under /path
One important note is that ZooKeeper does not allow partial writes or reads of the znode data. When setting the data of a znode or reading it, the content of the znode is replaced or read entirely.
```


ZooKeeper clients connect to a ZooKeeper service and establish a session through which they make API calls. 

If a worker becomes unavailable, its session expires and its znode in /workers disappears automatically.

An ephemeral znode can be deleted in two situations:
1. When the session of the client creator ends, either by expiration or because it ex‐ plicitly closed.
2. When a client, not necessarily the creator, deletes it.

### Sequential znodes
A znode can also be set to be sequential. A sequential znode is assigned a unique, mo‐ notonically increasing integer. This sequence number is appended to the path used to create the znode. For example, if a client creates a sequential znode with the path /tasks/ task-, ZooKeeper assigns a sequence number, say 1, and appends it to the path. The path of the znode becomes /tasks/task-1. Sequential znodes provide an easy way to create znodes with unique names. They also provide a way to easily see the creation order of znodes.

### watch
This is a common problem with polling. To replace the client polling, we have opted for a mechanism based on notifications: clients register with ZooKeeper to receive notifi‐ cations of changes to znodes. Registering to receive a notification for a given znode consists of setting a watch. A watch is a one-shot operation, which means that it triggers one notification. To receive multiple notifications over time, the client must set a new watch upon receiving each notification. 

## Versions
Each znode has a version number associated with it that is incremented every time its data changes. A couple of operations in the API can be executed conditionally: setDa ta and delete. Both calls take a version as an input parameter, and the operation suc‐ ceeds only if the version passed by the client matches the current version on the server. The use of versions is important when multiple ZooKeeper clients might be trying to perform operations over the same znode. For example, suppose that a client c1 writes a znode /config containing some configuration. If another client c2 concurrently updates the znode, the version c1 has is stale and the setData of c1 must not succeed. Using versions avoids such situations. In this case, the version that c1 uses when writing back doesn’t match and the operation fails. 

# ZooKeeper Architecture
Now that we have discussed at a high level the operations that ZooKeeper exposes to applications, we need to understand more of how the service actually works. Applica‐ tions make calls to ZooKeeper through a client library. The client library is responsible for the interaction with ZooKeeper servers.

ZooKeeper servers run in two modes: standalone and quorum. Standalone mode is pretty much what the term says: there is a single server, and ZooKeeper state is not replicated. In quorum mode, a group of ZooKeeper servers, which we call a ZooKeeper ensemble, replicates the state, and together they serve client requests. From this point on, we use the term “ZooKeeper ensemble” to denote an installation of servers. This installation could contain a single server and operate in standalone mode or contain a group of servers and operate in quorum mode.

## ZooKeeper Quorums
In quorum mode, ZooKeeper replicates its data tree across all servers in the ensemble. But if a client had to wait for every server to store its data before continuing, the delays might be unacceptable. In public administration, a quorum is the minimum number of legislators required to be present for a vote. In ZooKeeper, it is the minimum number of servers that have to be running and available in order for ZooKeeper to work. This number is also the minimum number of servers that have to store a client’s data before telling the client it is safely stored. For instance, we might have five ZooKeeper servers in total, but a quorum of three. So long as any three servers have stored the data, the client can continue, and the other two servers will eventually catch up and store the data.

It is important to choose an adequate size for the quorum. Quorums must guarantee that, regardless of delays and crashes in the system, any update request the service pos‐ itively acknowledges will persist until another request supersedes it.

`The bottom line is that we should always shoot for an odd number of servers.`


## sessions

All operations a client submits to ZooKeeper are associated to a session. When a session ends for any reason, the ephemeral nodes created during that session disappear.

the session may be moved to a different server if the client has not heard from its current server for some time. Moving a session to a different server is handled transparently by the ZooKeeper client library.

Sessions offer order guarantees, which means that requests in a session are executed in FIFO (first in, first out) order. Typically, a client has only a single session open, so its requests are all executed in FIFO order. If a client has multiple concurrent sessions, FIFO ordering is not necessarily preserved across the sessions.


## Commands
```sh
[zk: 127.0.0.1:2181,127.0.0.1:2182(CONNECTED) 5] stat /master
cZxid = 0x4
ctime = Mon Aug 20 21:10:23 AEST 2018
mZxid = 0x4
mtime = Mon Aug 20 21:10:23 AEST 2018
pZxid = 0x4
cversion = 0
dataVersion = 0
aclVersion = 0
ephemeralOwner = 0x10003c70e250001
dataLength = 11
numChildren = 0


[zk: 127.0.0.1:2181,127.0.0.1:2182(CONNECTED) 8] create /workers ""
Created /workers
[zk: 127.0.0.1:2181,127.0.0.1:2182(CONNECTED) 9] create /tasks ""
Created /tasks
[zk: 127.0.0.1:2181,127.0.0.1:2182(CONNECTED) 10] create /assign ""
Created /assign
[zk: 127.0.0.1:2181,127.0.0.1:2182(CONNECTED) 11] ls /
[assign, master, tasks, workers, zookeeper]

```





