---
header:
    image: /assets/images/2025-01-11-bushifire.jpeg
title:  Aewsome Apache Flink Architecture
date: 2025-01-12
tags:
 - news
- fires
 
permalink: /blogs/tech/en/awesome-apache-flink-architecture
layout: single
category: tech
---

> "The flame that burns twice as bright burns half as long." - Lao Tzu

TaskManagers, containers, and slots in Apache Flink's architecture explained

A container typically contains one TaskManager - this is the standard deployment pattern. Here's the typical topology from top to bottom:

1. Virtual Machine (VM) level:
- One VM can host multiple containers
- The VM provides the base computing resources

2. Container level:
- Each container usually runs one TaskManager
- The container provides isolation and resource management
- This is commonly deployed using Docker or Kubernetes

3. TaskManager level:
- One TaskManager per container is the standard pattern
- The TaskManager manages its allocated resources
- It communicates with the JobManager for task coordination

4. Slot level:
- Each TaskManager is divided into multiple task slots
- Slots are the smallest resource unit in Flink
- The number of slots is configurable (commonly 1-4 slots per TaskManager)
- Each slot can run one or more subtasks from the same job

For example, a typical setup might look like:
```
VM
└── Container 1
    └── TaskManager 1
        ├── Slot 1
        ├── Slot 2
        └── Slot 3
└── Container 2
    └── TaskManager 2
        ├── Slot 1
        ├── Slot 2
        └── Slot 3
```

Would you like me to explain any specific aspect of this topology in more detail?

## exactly-once state consistency

Flink guarantees exactly-once state consistency in case of failures by periodically and asynchronously checkpointing the local state to durable storage. This allows Flink to recover the state in case of failures and resume processing from the last successful checkpoint. The checkpointing mechanism is designed to be lightweight and efficient, ensuring minimal impact on the processing latency.
