---
title: JVM wram up
---

# JVM wram up
Keeping this in mind, for low-latency applications, we need to cache all classes beforehand – so that they’re available instantly when accessed at runtime.

This process of tuning the JVM is known as warming up.


# Escape Analysis

Escape analysis is a technique by which the Java Hotspot Server Compiler can analyze the scope of a new object's uses and decide whether to allocate it on the Java heap.

Based on escape analysis, an object's escape state might be one of the following:

* GlobalEscape – An object escapes the method and thread. For example, an object stored in a static field, or, stored in a field of an escaped object, or, returned as the result of the current method.
* ArgEscape – An object passed as an argument or referenced by an argument but does not globally escape during a call. This state is determined by analyzing the bytecode of called method.
* NoEscape – A scalar replaceable object, meaning its allocation could be removed from generated code.


After escape analysis, the server compiler eliminates scalar replaceable object allocations and associated locks from generated code. The server compiler also eliminates locks for all non-globally escaping objects. It does not replace a heap allocation with a stack allocation for non-globally escaping objects.


The JIT aggressively inlines methods, removing the overhead of method calls. Methods that can be inlined include static, private or final methods but also public methods if it can be determined that they are not overridden. Because of this, subsequent class loading can invalidate the previously generated code. Because inlining every method everywhere would take time and would generate an unreasonably big binary, the JIT compiler inlines the hot methods first until it reaches a threshold. To determine which methods are hot, the JVM keeps counters to see how many times a method is called and how many loop iterations it has executed. This means that inlining happens only after a steady state has been reached, so you need to repeat the operations a certain number of times before there is enough profiling information available for the JIT compiler to do its job.

Rather than trying to guess what the JIT is doing, you can take a peek at what’s happening by turning on java command line flags: -XX:+PrintCompilation -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining

Here is what they do:

    -XX:+PrintCompilation: logs when JIT compilation happens
    -XX:+UnlockDiagnosticVMOptions: enables other flags like -XX:+PrintInlining





GlobalEscape and ArgEscape objects must be allocated on the heap, but for ArgEscape objects it is possible to remove some locking and memory synchronization overhead because these objects are only visible from the calling thread.

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

