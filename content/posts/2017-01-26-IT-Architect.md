---
layout: page
title: IT-Architect
tags:
- Architect
- Questions
---

# SOA
- SOA is a set of design principles for building a suite of interoperable, flexible and reusable services based architecture.
- top-down and bottom-up approach SOA patterns

# Design Patterns
## Singleton
- Being single sometimes has its advantages you know. I’m often used to manage pools of resources, like connection or thread pools.
- The Singleton Pattern ensures a class has only one instance, and provides **a global point of access to it**.
- WATCH IT!
**Double-checked locking doesn’t work in Java 1.4 or earlier**!
Unfortunately, in Java version 1.4 and earlier, many JVMs contain implementations of the **volatile keyword that allow improper synchronization for double-checked locking**. If you must use a JVM earlier than Java 5, consider other methods of implementing your Singleton.

# Reference 
