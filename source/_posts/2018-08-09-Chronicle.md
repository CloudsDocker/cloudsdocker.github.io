---
title: Chronicle
---
# Low GC 
Ultra low GC means less than one minor collection per day.

the principles of Zero-copy eliminating unnecessary garbage collection and increased speed. Runtime code generation that reduces code size for efficient CPU cache usage and increased speed. Smart ordering for optimal parsing and you guessed it increased speed. All these combine to allow Chronicle FIX to achieve excellent performance results.

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