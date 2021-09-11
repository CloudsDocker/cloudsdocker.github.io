---
title: Chronicle
layout: posts
---

# Overview

Chronicle Software is about simplifying fast data.  It is a suite of libraries to make it easier to write, monitor and tune data processing systems where performance and scalability are concerned.

# Writing to a Queue
In Chronicle Queue we refer to the act of writing your data to the Chronicle queue, as storing an excerpt. This data could be made up from any data type, including text, numbers, or serialised blobs. Ultimately, all your data, regardless of what it is, is stored as a series of bytes.

Just before storing your excerpt, Chronicle Queue reserves an 8-byte header. Chronicle Queue writes the length of your data into this header. This way, when Chronicle Queue comes to read your excerpt, it knows how long each blob of data is. We refer to this 8-byte header, along with your excerpt, as a document. So strictly speaking Chronicle Queue can be used to read and write documents.

> Within this 8-byte header we also reserve a few bits for a number of internal operations, such as locking, to make Chronicle Queue thread-safe across both processors and threads. The important thing to note is that because of this, you can’t strictly convert the 8 bytes to an integer to find the length of your data blob.

To write data to a Chronicle-Queue, you must first create an Appender

```java
try (ChronicleQueue queue = SingleChronicleQueueBuilder.binary(path + "/trades").build()) {
   final ExcerptAppender appender = queue.acquireAppender();
}
```
Chronicle Queue uses the following low-level interface to write the data:
```java
try (final DocumentContext dc = appender.writingDocument()) {
      dc.wire().write().text(“your text data“);
}
```
So, Chronicle Queue uses an `Appender to write` to the queue and a `Tailer to read` from the queue. Unlike other java queuing solutions, messages are not lost when they are read with a Tailer. 

Each Chronicle Queue excerpt has a unique index.

```java
try (final DocumentContext dc = appender.writingDocument()) {
    dc.wire().write().text(“your text data“);
    System.out.println("your data was store to index="+ dc.index());
}
```

The high-level methods below such as writeText() are convenience methods on calling appender.writingDocument(), but both approaches essentially do the same thing. The actual code of writeText(CharSequence text) looks like this:

```java
/**
 * @param text to write a message
 */
void writeText(CharSequence text) {
    try (DocumentContext dc = writingDocument()) {
        dc.wire().bytes().append8bit(text);
    }
}

```

This is the highest-level API which hides the fact you are writing to messaging at all. The benefit is that you can swap calls to the interface with a real component, or an interface to a different protocol.
```java
// using the method writer interface.
RiskMonitor riskMonitor = appender.methodWriter(RiskMonitor.class);
final LocalDateTime now = LocalDateTime.now(Clock.systemUTC());
riskMonitor.trade(new TradeDetails(now, "GBPUSD", 1.3095, 10e6, Side.Buy, "peter"));
```

You can write a "self-describing message". Such messages can support schema changes. They are also easier to understand when debugging or diagnosing problems.
```java
// writing a self describing message
appender.writeDocument(w -> w.write("trade").marshallable(
        m -> m.write("timestamp").dateTime(now)
                .write("symbol").text("EURUSD")
                .write("price").float64(1.1101)
                .write("quantity").float64(15e6)
                .write("side").object(Side.class, Side.Sell)
                .write("trader").text("peter")));
```

You can write "raw data" which is self-describing. The types will always be correct; position is the only indication as to the meaning of those values.
```java
// writing just data
appender.writeDocument(w -> w
        .getValueOut().int32(0x123456)
        .getValueOut().int64(0x999000999000L)
        .getValueOut().text("Hello World"));
```
You can write "raw data" which is not self-describing. Your reader must know what this data means, and the types that were used.
```java
// writing raw data
appender.writeBytes(b -> b
        .writeByte((byte) 0x12)
        .writeInt(0x345678)
        .writeLong(0x999000999000L)
        .writeUtf8("Hello World"));
```
This is the lowest level way to write data. You get an address to raw memory and you can write what you want.
```java
// Unsafe low level
appender.writeBytes(b -> {
    long address = b.address(b.writePosition());
    Unsafe unsafe = UnsafeMemory.UNSAFE;
    unsafe.putByte(address, (byte) 0x12);
    address += 1;
    unsafe.putInt(address, 0x345678);
    address += 4;
    unsafe.putLong(address, 0x999000999000L);
    address += 8;
    byte[] bytes = "Hello World".getBytes(StandardCharsets.ISO_8859_1);
    unsafe.copyMemory(bytes, Unsafe.ARRAY_BYTE_BASE_OFFSET, null, address, bytes.length);
    b.writeSkip(1 + 4 + 8 + bytes.length);
});
```
You can print the contents of the queue. You can see the first two, and last two messages store the same data.

// dump the content of the queue
System.out.println(queue.dump());
# position: 262568, header: 0
--- !!data #binary
trade: {
  timestamp: 2016-07-17T15:18:41.141,
  symbol: GBPUSD,
  price: 1.3095,
  quantity: 10000000.0,
  side: Buy,
  trader: peter
}
# position: 262684, header: 1
--- !!data #binary
trade: {
  timestamp: 2016-07-17T15:18:41.141,
  symbol: EURUSD,
  price: 1.1101,
  quantity: 15000000.0,
  side: Sell,
  trader: peter
}
# position: 262800, header: 2
--- !!data #binary
!int 1193046
168843764404224
Hello World
# position: 262830, header: 3
--- !!data #binary
000402b0       12 78 56 34 00 00  90 99 00 90 99 00 00 0B   ·xV4·· ········
000402c0 48 65 6C 6C 6F 20 57 6F  72 6C 64                Hello Wo rld
# position: 262859, header: 4
--- !!data #binary
000402c0                                               12                 ·
000402d0 78 56 34 00 00 90 99 00  90 99 00 00 0B 48 65 6C xV4····· ·····Hel
000402e0 6C 6F 20 57 6F 72 6C 64 

## Finding the index at the end of a Chronicle Queue

Chronicle Queue appenders are thread-local. In fact when you ask for:
```java
final ExcerptAppender appender = queue.acquireAppender();
```
the acquireAppender() uses a thread-local pool to give you an appender which will be reused to reduce object creation.

As such, the method call to:
```java
long index = appender.lastIndexAppended();
```
will only give you the last index appended by this appender; not the last index appended by any appender.

If you wish to find the index of the last record written, then you have to call:
```java
long index = queue.createTailer().toEnd().index();
```

## Dumping a Chronicle Queue, cq4 file as text to the Command Line

Chronicle Queue stores its data in binary format, with a file extension of cq4:

\��@π�header∂�SCQStoreÇE���»wireType∂�WireTypeÊBINARYÕwritePositionèèèèß��������ƒroll∂�SCQSRollÇ*���∆length¶ÄÓ6�∆format
ÎyyyyMMdd-HH≈epoch¶ÄÓ6�»indexing∂SCQSIndexingÇN��� indexCount•��ÃindexSpacing�Àindex2Indexé����ß��������…lastIndexé�
���ß��������ﬂlastAcknowledgedIndexReplicatedé������ßˇˇˇˇˇˇˇˇ»recovery∂�TimedStoreRecoveryÇ����…timeStampèèèß����������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������������
This can often be a bit difficult to read, so it is better to dump the cq4 files as text. This can also help you fix your production issues, as it gives you the visibility as to what has been stored in the queue, and in what order.

You have to use the chronicle-queue.jar, from any version 4.5.3 or later, and set up the dependent files in the class path. 


$ java -cp chronicle-queue-4.5.5.jar net.openhft.chronicle.queue.DumpQueueMain 19700101-02.cq4

this will dump the 19700101-02.cq4 file out as text, as shown below:

--- !!meta-data #binary
header: !SCQStore {
  wireType: !WireType BINARY,
  writePosition: 0,
  roll: !SCQSRoll {
    length: !int 3600000,
    format: yyyyMMdd-HH,
    epoch: !int 3600000
  },
  indexing: !SCQSIndexing {
    indexCount: !short 4096,
    indexSpacing: 4,
    index2Index: 0,
    lastIndex: 0
  },
  lastAcknowledgedIndexReplicated: -1,
  recovery: !TimedStoreRecovery {
    timeStamp: 0
  }
}

...
4198044 bytes remaining

## Reading from a Queue using a Tailer

Reading the queue follows the same pattern as writing, except there is a possibility there is not a message when you attempt to read it.

Start Reading
```java
try (ChronicleQueue queue = SingleChronicleQueueBuilder.binary(path + "/trades").build()) {
   final ExcerptTailer tailer = queue.createTailer();
}
```

You can turn each message into a method call based on the content of the message.
```java
// reading using method calls
RiskMonitor monitor = System.out::println;
MethodReader reader = tailer.methodReader(monitor);
// read one message
assertTrue(reader.readOne());
```
You can decode the message yourself.
```java
assertTrue(tailer.readDocument(w -> w.read("trade").marshallable(
        m -> {
            LocalDateTime timestamp = m.read("timestamp").dateTime();
            String symbol = m.read("symbol").text();
            double price = m.read("price").float64();
            double quantity = m.read("quantity").float64();
            Side side = m.read("side").object(Side.class);
            String trader = m.read("trader").text();
            // do something with values.
        })));
```

You can read self-describing data values. This will check the types are correct, and convert as required.
```java

assertTrue(tailer.readDocument(w -> {
    ValueIn in = w.getValueIn();
    int num = in.int32();
    long num2 = in.int64();
    String text = in.text();
    // do something with values
}));
```

You can read raw data as primitives and strings.

```java
assertTrue(tailer.readBytes(in -> {
    int code = in.readByte();
    int num = in.readInt();
    long num2 = in.readLong();
    String text = in.readUtf8();
    assertEquals("Hello World", text);
    // do something with values
}));
```

or, you can get the underlying memory address and access the native memory.

```java
assertTrue(tailer.readBytes(b -> {
    long address = b.address(b.readPosition());
    Unsafe unsafe = UnsafeMemory.UNSAFE;
    int code = unsafe.getByte(address);
    address++;
    int num = unsafe.getInt(address);
    address += 4;
    long num2 = unsafe.getLong(address);
    address += 8;
    int length = unsafe.getByte(address);
    address++;
    byte[] bytes = new byte[length];
    unsafe.copyMemory(null, address, bytes, Unsafe.ARRAY_BYTE_BASE_OFFSET, bytes.length);
    String text = new String(bytes, StandardCharsets.UTF_8);
    assertEquals("Hello World", text);
    // do something with values
}));
```
### Tailers and File Handlers Clean up

Chronicle queue tailers may create file handlers, the file handlers are cleaned up whenever the associated chronicle queue is close() or whenever the Jvm runs a Garbage Collection. 

### ExcerptTailer.toEnd()

In some applications, it may be necessary to start reading from the end of the queue (e.g. in a restart scenario). For this use-case, ExcerptTailer provides the toEnd() method.

If it is necessary to read backwards through the queue from the end, then the tailer can be set to read backwards:
```java
ExcerptTailer tailer = queue.createTailer();
tailer.direction(TailerDirection.BACKWARD).toEnd();
```

When reading backwards, then the toEnd() method will move the tailer to the last record in the queue. If the queue is not empty, then there will be a DocumentContext available for reading:
```java
// this will be true if there is at least one message in the queue
boolean messageAvailable = tailer.toEnd().direction(TailerDirection.BACKWARD).
        readingDocument().isPresent();
```


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

public interface BytesStore extends RandomDataInput, RandomDataOutput, ReferencedCount, CharSequence

public interface Memory {
    default long heapUsed() {
        Runtime runtime = Runtime.getRuntime();
        return runtime.totalMemory() - runtime.freeMemory();
    }


    @Override
    @ForceInline
    public void writeByte(long address, byte b) {
        UNSAFE.putByte(address, b);
    }


/**
 * Marker annotation for some methods and constructors in the JSR 292 implementation.
 * <p>
 * To utilise this annotation se Chronicle Enterprise Warmup module.
 */
@Target({ElementType.METHOD, ElementType.CONSTRUCTOR})
@Retention(RetentionPolicy.RUNTIME)
public @interface ForceInline {
}

# Reference
- https://github.com/OpenHFT/Chronicle-Queue
- http://vanillajava.blogspot.com/2015/08/what-does-chronicle-software-do.html
