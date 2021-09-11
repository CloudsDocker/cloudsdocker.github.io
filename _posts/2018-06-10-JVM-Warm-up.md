---
title: JVM warm up by Escape Analysis
weight: 500
date: 2020-03-28
tags:
- JVM warm up
- Java
- Low latency
layout: posts
---

# Why JVM need warm up
I don't know how and why you get to this blog. But I know the key words in your mind are "warm" for JVM. As the name "warm up" suggested, and like what you normally do before work out. Warm up means **get your body/system ready and tune it to perfect state**
As for systems running under JVM, if they are time critical and latency sensitive. The best approach to make it run in good state is good preparation. 

One feasible strategy for low-latency applications, we need to cache all classes beforehand – so that they’re available instantly when accessed at runtime.

This process of tuning the JVM is known as warming up.

There are multiple tools & approach to implement warm up, while I'm going to dig into one of most important **strategy to warm up your application in JVM. That's EA: Escape Analysis**.

## Escape Analysis

 Java objects are created and stored in the heap. The programming language does not offer the possibility to let the programmer decide if an object should be generated in the stack. But in certain cases it would be desirable to allocate an object on the stack, as the memory allocation on the stack is cheaper than the memory allocation in the heap, deallocation on the stack is free and the stack is efficiently managed by the runtime.

The JVM uses therefore internally escape analysis to check if an object is used only with a thread or method. If the JVM identify this it may decide to create the object on the stack, increasing performance of the Java program.


Escape analysis is a technique by which the Java Hotspot Server Compiler can analyze the scope of a new object's uses and decide whether to allocate it on the Java heap.

### Why EA help to boost application performance in JVM?

As you know, JVM will allocate memory space in different sections. They performs significanlty different, normally heap is slower than stack, which is even slower than CPU registers.
So to improve system performance, we'd put our data step away from _heap_. 
When your java source code being compiled, JIT will leverage Escape Analysis to allocate space on the method stack or even in CPU registers instead of Java heap space. This is a very important performance optimization because stack allocation and de-allocation are much faster than heap space allocation.

### How escape analysis work

Based on escape analysis during JIT, an object's escape state might be one of the following:

* GlobalEscape – An object escapes the method and thread. For example, an object stored in a static field, or, stored in a field of an escaped object, or, returned as the result of the current method.
* ArgEscape – An object passed as an argument or referenced by an argument but does not globally escape during a call. This state is determined by analyzing the bytecode of called method.
* NoEscape – A scalar replaceable object, meaning its allocation could be removed from generated code.


After escape analysis, the server compiler eliminates scalar replaceable object allocations and associated locks from generated code. The server compiler also eliminates locks for all non-globally escaping objects. 

Please beadvised it does not replace a heap allocation with a stack allocation for non-globally escaping objects.

## JIT inline optimisation

The JIT aggressively inlines methods, removing the overhead of method calls. Methods that can be inlined include static, private or final methods but also public methods if it can be determined that they are not overridden. 

Because of this, subsequent class loading can invalidate the previously generated code. Because inlining every method everywhere would take time and would generate an unreasonably big binary, the JIT compiler inlines the hot methods first until it reaches a threshold. 
To determine which methods are hot, the JVM keeps counters to see how many times a method is called and how many loop iterations it has executed. This means that inlining happens only after a steady state has been reached, so you need to repeat the operations a certain number of times before there is enough profiling information available for the JIT compiler to do its job.

Rather than trying to guess what the JIT is doing, you can take a peek at what’s happening by turning on java command line flags: -XX:+PrintCompilation -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining

Here is what they do:

    -XX:+PrintCompilation: logs when JIT compilation happens
    -XX:+UnlockDiagnosticVMOptions: enables other flags like -XX:+PrintInlining




### Improve performance by removing locking 
As you konw, **Lock** would significantely slow down or even freeze your application running in JVM.

During Escape analysis. GlobalEscape and ArgEscape objects must be allocated on the heap, but for ArgEscape objects it is possible to remove some locking and memory synchronization overhead because these objects are only visible from the calling thread.

The NoEscape objects may be allocated freely, for example on the stack instead of on the heap. In fact, under some circumstances, it is not even necessary to construct an object at all, but instead only the object's scalar values, such as an int for the object Integer. Synchronization may be removed too, because we know that only this thread will use the objects. For example, if we were to use the somewhat ancient StringBuffer (which as opposed to StringBuilder has synchronized methods), then these synchronizations could safely be removed.

EA is currently only available under the C2 HotSpot Compiler so we have to make sure that we run in -server mode.


## Why It Matters
In theory, NoEscape objects objects can be allocated on the stack or even in CPU registers using EA,  giving very fast execution.

When we allocate objects on the heap, we start to drain our CPU caches because objects are placed on different addresses on the heap possibly far away from each other. This way we will quickly deplete our L1 CPU cache and performance will decrease. With EA and stack allocation on the other hand, we are using memory that (most likely) is already in the L1 cache anyhow.  So, EA and stack allocation will improve our localization of data. This is good from a performance standpoint.

Obviously, the garbage collects needs to run much less frequently when we are using EA with stack allocation. This is perhaps the biggest performance advantage. Recall that each time the JVM runs a complete heap scan, we take performance out of our CPUs and the CPU caches will quickly deplete. Not to mention if we have virtual memory paged out on our server, whereby GC is devastating for performance.

The most important advantage of EA is not performance though. EA allows us to use local abstractions like Lambdas, Functions, Streams, Iterators etc. without any significant performance penalty so that we can write better and more readable code. Code that describes what we are doing rather than how it is done.


The GC cleans up the heap and not the stack. The stack is cleaned up automatically when methods return to their caller whereby the stack pointer is reset to its former value. So GC will clean up objects that ended up on the stack before EA/C2 compilation could be performed. The actual instances (or rather their corresponding representations) live on the stack, there are no referenced objects on the stack in the context of EA optimizations.

# JIT optimization

Some JIT Compilation Techniques

One of the most common JIT compilation techniques used by Java HotSpot VM is inlining, which is the practice of substituting the body of a method into the places where that method is called. Inlining saves the cost of calling the method; no new stack frames need to be created. By default, Java HotSpot VM will try to inline methods that contain less than 35 bytes of JVM bytecode.

Another common optimization that Java HotSpot VM makes is monomorphic dispatch, which relies on the observed fact that, usually, there aren’t paths through a method that cause an object reference to be of one type most of the time but of another type at other times.

You might think that having different types via different code paths would be ruled out by Java’s static typing, but remember that an instance of a subtype is always a valid instance of a supertype (this principle is known as the Liskov substitution principle, after Barbara Liskov). This situation means that there could be two paths into a method—for example, one that passes an instance of a supertype and one that passes an instance of a subtype—which would be legal by the rules of Java’s static typing (and does occur in practice).

In the usual case (the monomorphic case), however, having different, path-dependent types does not happen. So we know the exact method definitions that will be called when methods are called on the passed object, because we don’t need to check which override is actually being used. This means we can eliminate the overhead of doing virtual method lookup, so the JIT compiler can emit optimized machine code that is often faster than an equivalent C++ call (because in the C++ case, the virtual lookup cannot easily be eliminated).
The two Java HotSpot VM compiler modes use different techniques for JIT compilation, and they can output very different machine code for the same Java method. Modern Java applications, however, can usually make use of both compilation modes.

Java HotSpot VM uses many other techniques to optimize the code that JIT compilation produces. Loop optimization, type sharpening, dead-code elimination, and intrinsics are just some of the other ways that Java HotSpot VM tries to optimize code as much as it can. Techniques are frequently layered one on top of another, so that once one optimization has been applied, the compiler might be able to see more optimizations that can be performed.

# Compilation Modes

Inside Java HotSpot VM, there are actually two separate JIT compiler modes, which are known as C1 and C2. C1 is used for applications where quick startup and rock-solid optimization are required; GUI applications are often good candidates for this compiler. C2, on the other hand, was originally intended for long-running, predominantly server-side applications. Prior to some of the later Java SE 7 releases, these two modes were available using the -client and -server switches, respectively.

The two compiler modes use different techniques for JIT compilation, and they can output very different machine code for the same Java method. Modern Java applications, however, can usually make use of both compilation modes. To take advantage of this fact, starting with some of the later Java SE 7 releases, a new feature called tiered compilation became available. This feature uses the C1 compiler mode at the start to provide better startup performance. Once the application is properly warmed up, the C2 compiler mode takes over to provide more-aggressive optimizations and, usually, better performance. With the arrival of Java SE 8, tiered compilation is now the default behavior.


# Java memory monitoring tools

```bash

pemi$ jps | grep Main
50903 Main
pemi$ jmap -histo 50903 | head
 num     #instances         #bytes  class name

----------------------------------------------
   1:            95       42952184  [I
   2:          1079         101120  [C
   3:           485          55272  java.lang.Class
   4:           526          25936  [Ljava.lang.Object;
   5:            13          25664  [B
   6:          1057          25368  java.lang.String
   7:            74           5328  java.lang.reflect.Field
```

jmap - Memory Map



Tool or Option  Description and Usage

Java Mission Control
    

Java Mission Control (JMC) is a new JDK profiling and diagnostic tools platform for HotSpot JVM. It s a tool suite basic monitoring, managing, and production time profiling and diagnostics with high performance. Java Mission Control minimizes the performance overhead that's usually an issue with profiling tools. See Java Mission Control.

jcmd utility
    

The jcmd utility is used to send diagnostic command requests to the JVM, where these requests are useful for controlling Java Flight Recordings. The JFRs are used to troubleshoot and diagnose JVM and Java Applications with flight recording events. See The jcmd Utility.

Java VisualVM
    

This utility provides a visual interface for viewing detailed information about Java applications while they are running on a Java Virtual Machine. This information can be used in troubleshooting local and remote applications, as well as for profiling local applications. See Java VisualVM.

JConsole utility
    

This utility is a monitoring tool that is based on Java Management Extensions (JMX). The tool uses the built-in JMX instrumentation in the Java Virtual Machine to provide information about performance and resource consumption of running applications. See JConsole.

jmap utility
    

This utility can obtain memory map information, including a heap histogram, from a Java process, a core file, or a remote debug server. See The jmap Utility.

jps utility
    

This utility lists the instrumented Java HotSpot VMs on the target system. The utility is very useful in environments where the VM is embedded, that is, it is started using the JNI Invocation API rather than the java launcher. See The jps Utility.

jstack utility
    

This utility can obtain Java and native stack information from a Java process. On Oracle Solaris and Linux operating systems the utility can alos get the information from a core file or a remote debug server. See The jstack Utility.

jstat utility
    

This utility uses the built-in instrumentation in Java to provide information about performance and resource consumption of running applications. The tool can be used when diagnosing performance issues, especially those related to heap sizing and garbage collection. See The jstat Utility.

jstatd daemon
    

This tool is a Remote Method Invocation (RMI) server application that monitors the creation and termination of instrumented Java Virtual Machines and provides an interface to allow remote monitoring tools to attach to VMs running on the local host. See The jstatd Daemon.

visualgc utility
    

This utility provides a graphical view of the garbage collection system. As with jstat, it uses the built-in instrumentation of Java HotSpot VM. See The visualgc Tool.

Native tools
    

Each operating system has native tools and utilities that can be useful for monitoring purposes. For example, the dynamic tracing (DTrace) capability introduced in Oracle Solaris 10 operating system performs advanced monitoring. See Native Operating System Tools.




```bash
$ jps
16217 MyApplication
16342 jps

The utility lists the virtual machines for which the user has access rights. This is determined by access-control mechanisms specific to the operating system. On Oracle Solaris operating system, for example, if a non-root user executes the jps utility, then the output is a list of the virtual machines that were started with that user's uid.

In addition to listing the PID, the utility provides options to output the arguments passed to the application's main method, the complete list of VM arguments, and the full package name of the application's main class. The jps utility can also list processes on a remote system if the remote system is running the jstatd daemon.

```


# GC-less Java

Java Development without GC
All products developed by Coral Blocks have the very important feature of leaving ZERO garbage behind. Because the latency imposed by the Java Garbage Collector (i.e. GC) is unacceptable for high-performance systems and because it is impossible to turn off the GC, the best option for real-time systems in Java is to not produce any garbage at all so that the GC never kicks in. Imagine a high-performance matching engine operating in the microsecond level, sending and receiving hundreds of thousands messages per second. If at any given time the GC decides to kick in with its 1+ millisecond latencies, the disruption in the system will be huge. Therefore, if you want to develop real-time systems in Java with minimal variance and latency, the best option is to do it right without creating any garbage for the GC. 


## Warming up, Checking the GC and Sampling
The key to make sure your system is not creating any garbage is to warm up your critical path from start to finish a couple of million times and then check for memory allocation another couple of million times. If it is allocating memory linearly as the number of iterations increases, it is most likely creating garbage and you should use the stack trace 
