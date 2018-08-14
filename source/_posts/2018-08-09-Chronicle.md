---
title: Chronicle
---
# Low GC 
Ultra low GC means less than one minor collection per day.

the principles of Zero-copy eliminating unnecessary garbage collection and increased speed. Runtime code generation that reduces code size for efficient CPU cache usage and increased speed. Smart ordering for optimal parsing and you guessed it increased speed. All these combine to allow Chronicle FIX to achieve excellent performance results.

# Low garbage rate

Minimising garbage is key to avoiding GC pauses. To use your L1 and L2 cache efficiently, you need to keep your garbage rates very low.  If you are not using these cache efficiently your application can be 2-5x slower. 

The garbage from Chronicle is low enough that you can process one million events without jstat detecting you have created any garbage.  jstat only displays multiples of 4 KB, and only when a new TLAB is allocated.  Chronicle does create garbage, but it is extremely low. i.e. a few objects per million events processes.

Once you make the GC pauses manageable, or non-existent, you start to see other sources of delay in your system.   Take away the boulders and you start to see the rocks.  Take away the rocks and you start to see the pebbles.


# Chronicle has minimal interaction with the Operating System.

System calls are slow, and if you can avoid call the OS, you can save significant amounts of latency. 

For example, if you send a message over TCP on loopback, this can add a 10 micro-seconds latency between writing and reading the data.  You can write to a chronicle, which is a plain write to memory, and read from chronicle, which is also a read from memory with a latency of 0.2 micro-seconds. (And as I mentioned before, you get persistence as well)

# No need to worry about running out of heap.

A common problem with unbounded queues and this uses an open ended amount of heap.  

Chronicle solves this by not using the heap to store data, but instead using memory mapped files.  This improve memory utilisation by making the data more compact but also means a 1 GB JVM can stream 1 TB of data over a day without worrying about the heap or how much main memory you have.  In this case, an unbounded queue becomes easier to manage.

# how it works
Chronicle uses a memory mapped file to continuously journal messages, chronicles file-based storage will slowly grow in size as more data is written to the queue, the size of the queue can exceed your available memory, you are only constrained by the amount of disk space you have on your server. Chronicle writes data directly into off-heap memory which is shared between java processes on the same server.

Chronicle is very fast, it is able to write and read a message in just two microseconds with no garbage. Typically at the end of each day, you archive the queue and start the next day with a fresh empty queue.

# Chronicle Queue is a distributed unbounded persisted queue. 

Chronicle Queue:

supports asynchronous RMI and Publish/Subscribe interfaces with microsecond latencies.

passes messages between JVMs in under a microsecond (in optimised examples)

passes messages between JVMs on different machines via replication in under 10 microseconds (in optimised examples)

provides stable, soft, real time latencies into the millions of messages per second for a single thread to one queue; with total ordering of every event.

## Queue introduction

Chronicle Queue is a Java project focused on building a persisted low-latency messaging framework for high performance and critical applications.

Chronicle diagram 005
At first glance Chronicle Queue can be seen as simply another queue implementation. However, it has major design choices that should be emphasised.

Using non-heap storage options (RandomAccessFile), Chronicle Queue provides a processing environment where applications do not suffer from Garbage Collection (GC). When implementing high-performance and memory-intensive applications (you heard the fancy term "bigdata"?) in Java, one of the biggest problems is garbage collection.

Garbage collection may slow down your critical operations non-deterministically at any time. In order to avoid non-determinism, and escape from garbage collection delays, off-heap memory solutions are ideal. The main idea is to manage your memory manually so it does not suffer from garbage collection. Chronicle Queue behaves like a management interface over off-heap memory so you can build your own solutions over it.

Chronicle Queue uses RandomAccessFiles while managing memory and this choice brings lots of possibilities. RandomAccessFiles permit non-sequential, or random, access to a file’s contents. To access a file randomly, you open the file, seek a particular location, and read from or write to that file. RandomAccessFiles can be seen as "large" C-type byte arrays that you can access at any random index "directly" using pointers. File portions can be used as ByteBuffers if the portion is mapped into memory.

This memory mapped file is also used for exceptionally fast interprocess communication (IPC) without affecting your system performance. There is no garbage collection as everything is done off-heap.


## Message type
- TCP: Stream-oriented 
- UDP, SCTP: message-oriented .

## On heap vs off heap memory usage
Overview

I was recently asked about the benefits and wisdom of using off heap memory in Java.  The answers may be of interest to others facing the same choices.

Off heap memory is nothing special.  The thread stacks, application code, NIO buffers are all off heap.  In fact in C and C++, you only have unmanaged memory as it does not have a managed heap by default.  The use of managed memory or "heap" in Java is a special feature of the language. Note: Java is not the only language to do this.
new Object() vs Object pool vs Off Heap memory.

new Object()

Before Java 5.0, using object pools was very popular.  Creating objects was still very expensive.   However, from Java 5.0, object allocation and garbage cleanup was made much cheaper, and developers found they got a performance speed up and a simplification of their code by removing object pools and just creating new objects whenever needed.  Before Java 5.0, almost any object pool, even an object pool which used objects provided an improvement, from Java 5.0 pooling only expensive objects obviously made sense e.g. threads, socket and database connections.

Object pools

In the low latency space it was still apparent that recycling mutable objects improved performance by reduced pressure on your CPU caches.  These objects have to have simple life cycles and have a simple structure, but you could see significant improvements in performance and jitter by using them. 
Another area where it made sense to use object pools is when loading large amounts of data with many duplicate objects. With a significant reduction in memory usage and a reduction in the number of objects the GC had to manage, you saw a reduction in GC times and an increase in throughput.
These object pools were designed to be more light weight than say using a synchronized HashMap, and so they still helped.

Take this StringInterner class as an example. You pass it a recycled mutable StringBuilder of the text you want as a String and it will provide a String which matches.  Passing a String would be inefficient as you would have already created the object.  The StringBuilder can be recycled.
Note: this structure has an interesting property that requires no additional thread safety features, like volatile or synchronized, other than is provided by the minimum Java guarantees. i.e. you can see the final fields in a String correctly and only read consistent references.

public class StringInterner {
    private final String[] interner;
    private final int mask;
    public StringInterner(int capacity) {
        int n = Maths.nextPower2(capacity, 128);
        interner = new String[n];
        mask = n - 1;
    }

    private static boolean isEqual(@Nullable CharSequence s, @NotNull CharSequence cs) {
        if (s == null) return false;
        if (s.length() != cs.length()) return false;
        for (int i = 0; i < cs.length(); i++)
            if (s.charAt(i) != cs.charAt(i))
                return false;
        return true;
    }

    @NotNull
    public String intern(@NotNull CharSequence cs) {
        long hash = 0;
        for (int i = 0; i < cs.length(); i++)
            hash = 57 * hash + cs.charAt(i);
        int h = (int) Maths.hash(hash) & mask;
        String s = interner[h];
        if (isEqual(s, cs))
            return s;
        String s2 = cs.toString();
        return interner[h] = s2;
    }
}
Off heap memory usage

Using off heap memory and using object pools both help reduce GC pauses, this is their only similarity.  Object pools are good for short lived mutable objects, expensive to create objects and long live immutable objects where there is a lot of duplication.  Medium lived mutable objects, or complex objects are more likely to be better left to the GC to handle.  However, medium to long lived mutable objects suffer in a number of ways which off heap memory solves.

Off heap memory provides;

Scalability to large memory sizes e.g. over 1 TB and larger than main memory.
Notional impact on GC pause times.
Sharing between processes, reducing duplication between JVMs, and making it easier to split JVMs.
Persistence for faster restarts or replying of production data in test.
The use of off heap memory gives you more options in terms of how you design your system.  The most important improvement is not performance, but determinism.

Off heap and testing

One of the biggest challenges in high performance computing is reproducing obscure bugs and being able to prove you have fixed them.  By storing all your input events and data off heap in a persisted way you can turn your critical systems into a series of complex state machines. (Or in simple cases, just one state machine) In this way you get reproducible behaviour and performance between test and production.

A number of investment banks use this technique to replay a system reliably to any event in the day and work out exactly why that event was processed the way it was.  More importantly, once you have a fix you can show that you have fixed the issue which occurred in production, instead of finding an issue and hoping this was the issue.

Along with deterministic behaviour comes deterministic performance.  In test environments, you can replay the events with realistic timings and show the latency distribution you expect to get in production.  Some system jitter can't be reproduce esp if the hardware is not the same, but you can get pretty close when you take a statistical view.  To avoid taking a day to replay a day of data you can add a threshold. e.g. if the time between events is more than 10 ms you might only wait 10 ms.  This can allow you to replay a day of events with realistic timing in under an hour and see whether your changes have improved your latency distribution or not.

By going more low level don't you lose some of "compile once, run anywhere"?

To some degree this is true, but it is far less than you might think.  When you are working closer the processor and so you are more dependant on how the processor, or OS behaves.  Fortunately, most systems use AMD/Intel processors and even ARM processors are becoming more compatible in terms of the low level guarantees they provide.  There is also differences in the OSes, and these techniques tend to work better on Linux than Windows.  However, if you develop on MacOSX or Windows and use Linux for production, you shouldn't have any issues.  This is what we do at Higher Frequency Trading.

What new problems are we creating by using off heap?

Nothing comes for free, and this is the case with off heap.  The biggest issue with off heap is your data structures become less natural.  You either need a simple data structure which can be mapped directly to off heap, or you have a complex data structure which serializes and deserializes to put it off heap.  Obvious using serialization has its own headaches and performance hit.  Using serialization thus much slower than on heap objects.

In the financial world, most high ticking data structure are flat and simple, full of primitives which maps nicely off heap with little overhead.

# How does Chronicle Queue work

## Terminology

- Messages are grouped by topics. A topic can contain any number of sub-topics which are logically stored together under the queue/topic.
- An appender is the source of messages.
- A tailer is a receiver of messages.
- Chronicle Queue is `broker-less` by default. You can use Chronicle Engine to act as a broker for remote access.

> Note
We deliberately avoid the term consumer as messages are not consumed/destroyed by reading.

## At a high level:

- appenders write to the end of a queue. There is no way to insert, or delete excerpts.

- tailers read the next available message each time they are called.

By using Chronicle Engine, a Java or C# client can publish to a queue to act as a remote appender, and you subscribe to a queue to act as a remote tailer.

## Topics and Queue files

Each topic is a directory of queues. There is a file for each roll cycle. If you have a topic called mytopic, the layout could look like this:

mytopic/
    20160710.cq4
    20160711.cq4
    20160712.cq4
    20160713.cq4
To copy all the data for a single day (or cycle), you can copy the file for that day on to your development machine for replay testing.

Appenders and tailers are cheap as they don’t even require a TCP connection; they are just a few Java objects.



## File Retention

You can add a StoreFileListener to notify you when a file is added, or no longer used. This can be used to delete files after a period of time. However, by default, files are retained forever. Our largest users have over 100 TB of data stored in queues.

## Every Tailer sees every message.

An abstraction can be added to filter messages, or assign messages to just one message processor. However, in general you only need one main tailer for a topic, with possibly, some supporting tailers for monitoring etc.

As Chronicle Queue doesn’t partition its topics, you get total ordering of all messages within that topic. Across topics, there is no guarantee of ordering; if you want to replay deterministically from a system which consumes from multiple topics, we suggest replaying from that system’s output.

# Guarantees

Chronicle Queue provides the following guarantees;

for each appender, messages are written in the order the appender wrote them. Messages by different appenders are interleaved,

for each tailer, it will see every message for a topic in the same order as every other tailer,

when replicated, every replica has a copy of every message.

# Use Cases

Chronicle Queue is most often used for producer-centric systems where you need to retain a lot of data for days or years.

## What is a producer-centric system?

Most messaging systems are consumer-centric. Flow control is implemented to avoid the consumer ever getting overloaded; even momentarily. A common example is a server supporting multiple GUI users. Those users might be on different machines (OS and hardware), different qualities of network (latency and bandwidth), doing a variety of other things at different times. For this reason it makes sense for the client consumer to tell the producer when to back off, delaying any data until the consumer is ready to take more data.

Chronicle Queue is a producer-centric solution and does everything possible to never push back on the producer, or tell it to slow down. This makes it a powerful tool, providing a big buffer between your system, and an upstream producer over which you have little, or no, control.

For market data in particular, real time means in a few microseconds; it doesn’t mean intra-day (during the day).

Chronicle Queue is fast and efficient, and has been used to increase the speed that data is passed between threads. In addition, it also keeps a record of every message passed allowing you to significantly reduce the amount of logging that you need to do.

## Latency Sensitive Micro-services

Chronicle Queue supports low latency IPC (Inter Process Communication) between JVMs on the same machine in the order of magnitude of 1 microsecond; as well as between machines with a typical latency of 10 microseconds for modest throughputs of a few hundred thousands. Chronicle Queue supports throughputs of millions of events per second, with stable microsecond latencies.

## Log Replacement

As Chronicle Queue can be used to build state machines. All the information about the state of those components can be reproduced externally, without direct access to the components, or to their state. This significantly reduces the need for additional logging.

However, any logging you do need can be recorded in great detail. This makes enabling DEBUG logging in production practical. This is because the cost of logging is very low; less than 10 microseconds. Logs can be replicated centrally for log consolidation.

Chronicle Queue is being used to store 100+ TB of data, which can be replayed from any point in time.

# Source code

## MappedFile
```java
package net.openhft.chronicle.bytes;

import net.openhft.chronicle.core.Jvm;
import net.openhft.chronicle.core.OS;
import net.openhft.chronicle.core.ReferenceCounted;
import net.openhft.chronicle.core.ReferenceCounter;
import net.openhft.chronicle.core.io.IORuntimeException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.lang.ref.WeakReference;
import java.nio.channels.FileChannel;
import java.nio.channels.FileChannel.MapMode;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import static net.openhft.chronicle.core.io.Closeable.closeQuietly;

/**
 * A memory mapped files which can be randomly accessed in chunks. It has overlapping regions to
 * avoid wasting bytes at the end of chunks.
 */
public class MappedFile implements ReferenceCounted {
    private static final long DEFAULT_CAPACITY = 128L << 40;
    // A single JVM cannot lock a file more than once.
    private static final Object GLOBAL_FILE_LOCK = new Object();
    @NotNull
    private final RandomAccessFile raf;
    private final FileChannel fileChannel;
```

# Reference
- https://github.com/OpenHFT/Chronicle-Queue
- 