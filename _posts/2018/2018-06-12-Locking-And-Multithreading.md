---
title: Locking and multithreading
tags:
- CAS
- Concurrent
layout: posts
---

# Single Writer principle

There is a lot of research in computer science for managing this contention that boils down to 2 basic approaches.  One is to provide mutual exclusion to the contended resource while the mutation takes place; the other is to take an optimistic strategy and swap in the changes if the underlying resource has not changed while you created the new copy.  

# Memory Barier

Memory barriers, or fences, are a set of processor instructions used to apply ordering limitations on memory operations. 


The keyword volatile prevents this problem because it establishes a happens before relationship between the write to the turn variable and the write to the intentFirst variable. The compiler cannot re-order these write operations and if necessary it must forbid the processor from doing so with a memory barrier.


A memory barrier, also known as a `membar`, `memory fence` or fence instruction, is a type of barrier instruction that causes a central processing unit (CPU) or compiler to enforce an ordering constraint on memory operations issued before and after the barrier instruction. This typically means that operations issued prior to the barrier are guaranteed to be performed before operations issued after the barrier.

Memory barriers are necessary because most modern CPUs employ performance optimizations that can result in out-of-order execution. This reordering of memory operations (loads and stores) normally goes unnoticed within a single thread of execution, but can cause unpredictable behaviour in concurrent programs and device drivers unless carefully controlled.


# Non blocking programing
Implementation
With few exceptions, non-blocking algorithms use atomic `read-modify-write` primitives that the hardware must provide, the most notable of which is compare and swap (CAS).

 
## Compare And Swap

It compares the contents of a memory location with a given value and, only if they are the same, modifies the contents of that memory location to a new given value. This is done as a single atomic operation. The atomicity guarantees that the new value is calculated based on up-to-date information; if the value had been updated by another thread in the meantime, the write would fail. The result of the operation must indicate whether it performed the substitution; this can be done either with a simple boolean response (this variant is often called compare-and-set), or by returning the value read from the memory location (not the value written to it).


Here is the pseudo code
``` C++
function cas(p : pointer to int, old : int, new : int) returns bool {
    if *p ≠ old {
        return false
    }
    *p ← new
    return true
}
```

This operation is used to implement synchronization primitives like semaphores and mutexes, as well as more sophisticated lock-free and wait-free algorithms.

Algorithms built around CAS typically read some key memory location and remember the old value. Based on that old value, they compute some new value. Then they try to swap in the new value using CAS, where the comparison checks for the location still being equal to the old value. If CAS indicates that the attempt has failed, it has to be repeated from the beginning: the location is re-read, a new value is re-computed and the CAS is tried again.


A common workaround is to add extra "tag" or "stamp" bits to the quantity being considered. For example, an algorithm using compare and swap on a pointer might use the low bits of the address to indicate how many times the pointer has been successfully modified. Because of this, the next compare-and-swap will fail, even if the addresses are the same, because the tag bits will not match. This does not completely solve the problem, as the tag bits will eventually wrap around, but helps to avoid it. Some architectures provide a double-word compare and swap, which allows for a larger tag. This is sometimes called ABAʹ since the second A is made slightly different from the first. Such tagged state references are also used in transactional memory.


## Priority Inversion

Consider two tasks H and L, of high and low priority respectively, either of which can acquire exclusive use of a shared resource R. If H attempts to acquire R after L has acquired it, then H becomes blocked until L relinquishes the resource. Sharing an exclusive-use resource (R in this case) in a well-designed system typically involves L relinquishing R promptly so that H (a higher priority task) does not stay blocked for excessive periods of time. Despite good design, however, it is possible that a third task M of medium priority (p(L) < p(M) < p(H), where p(x) represents the priority for task (x)) becomes runnable during L's use of R. At this point, M being higher in priority than L, preempts L, causing L to not be able to relinquish R promptly, in turn causing H—the highest priority process—to be unable to run. This is called priority inversion where a higher priority task is preempted by a lower priority one.



## RCU
In computer science, read-copy-update (RCU) is a synchronization mechanism based on mutual exclusion. It is used when performance of reads is crucial and is an example of space–time tradeoff, enabling fast operations at the cost of more space.

Read-copy-update allows multiple threads to efficiently read from shared memory by deferring updates after pre-existing reads to a later time while simultaneously marking the data, `ensuring new readers will read the updated data`. This makes all readers proceed as if there were no synchronization involved, hence they will be fast, but also making updates more difficult.


# package java/util/concurrent/atomic

A small toolkit of classes that support lock-free thread-safe programming on single variables. In essence, the classes in this package extend the notion of volatile

values, fields, and array elements to those that also provide an atomic conditional update operation of the form:
```java
   boolean compareAndSet(expectedValue, updateValue);
``` 

This method (which varies in argument types across different classes) atomically sets a variable to the updateValue if it currently holds the expectedValue, reporting true on success. The classes in this package also contain methods to get and unconditionally set values, as well as a weaker conditional atomic update operation weakCompareAndSet described below.

The specifications of these methods enable implementations to employ efficient machine-level atomic instructions that are available on contemporary processors. However on some platforms, support may entail some form of internal locking. Thus the methods are not strictly guaranteed to be non-blocking -- a thread may block transiently before performing the operation. 

Instances of classes AtomicBoolean, AtomicInteger, AtomicLong, and AtomicReference each provide access and updates to a single variable of the corresponding type. Each class also provides appropriate utility methods for that type. For example, classes AtomicLong and AtomicInteger provide atomic increment methods. One application is to generate sequence numbers, as in:
```java
 class Sequencer {
   private final AtomicLong sequenceNumber
     = new AtomicLong(0);
   public long next() {
     return sequenceNumber.getAndIncrement();
   }
 }
 ```

 The AtomicIntegerArray, AtomicLongArray, and AtomicReferenceArray classes further extend atomic operation support to arrays of these types. These classes are also notable in providing volatile access semantics for their array elements, which is not supported for ordinary arrays. 

# Volatile

 The Java volatile keyword is used to mark a Java variable as "being stored in main memory". More precisely that means, that every read of a volatile variable will be read from the computer's main memory, and not from the CPU cache, and that every write to a volatile variable will be written to main memory, and not just to the CPU cache. 

## What's wrong to volatile?

The Java `volatile keyword guarantees visibility of changes to variables across threads`. This may sound a bit abstract, so let me elaborate.

In a multithreaded application where the threads operate on non-volatile variables, each thread may copy variables from main memory into a CPU cache while working on them, for performance reasons. If your computer contains more than one CPU, each thread may run on a different CPU. That means, that each thread may copy the variables into the CPU cache of different CPUs. 

With non-volatile variables there are no guarantees about when the Java Virtual Machine (JVM) reads data from main memory into CPU caches, or writes data from CPU caches to main memory. This can cause several problems.

### visibility problem
The problem with threads not seeing the latest value of a variable because it has not yet been written back to main memory by another thread, is called a "visibility" problem. The updates of one thread are not visible to other threads. 

The Java volatile Visibility Guarantee

The Java volatile keyword is intended to address variable visibility problems. By declaring the counter variable volatile all writes to the counter variable will be written back to main memory immediately. Also, all reads of the counter variable will be read directly from main memory. 

###  Full volatile Visibility Guarantee

Actually, the visibility guarantee of Java volatile goes beyond the volatile variable itself. The visibility guarantee is as follows:

    If Thread A writes to a volatile variable and Thread B subsequently reads the same volatile variable, then all variables visible to Thread A before writing the volatile variable, will also be visible to Thread B after it has read the volatile variable.
    If Thread A reads a volatile variable, then all all variables visible to Thread A when reading the volatile variable will also be re-read from main memory.


### The Java volatile Happens-Before Guarantee

To address the instruction reordering challenge, the Java volatile keyword gives a "happens-before" guarantee, in addition to the visibility guarantee. The happens-before guarantee guarantees that:

- Reads from and writes to other variables cannot be reordered to occur `after` a write to a volatile variable, if the reads / writes originally occurred `before` the write to the volatile variable.

The reads / writes `before a write to a volatile` variable are guaranteed to `"happen before" the write to the volatile` variable. Notice that it is still possible for e.g. reads / writes of other variables located after a write to a volatile to be reordered to occur before that write to the volatile. Just not the other way around. `From after to before is allowed, but from before to after is not allowed`.

- Reads from and writes to other variables cannot be reordered to occur `before a read` of a volatile variable, if the reads / writes originally occurred `after the read` of the volatile variable. Notice that it is possible for reads of other variables that occur before the read of a volatile variable can be reordered to occur after the read of the volatile. Just not the other way around. `From before to after is allowed, but from after to before is not allowed`. 

- In short: ==before write,  after read==.

## Limitations of volatile 

Even if the volatile keyword guarantees that all reads of a volatile variable are read directly from main memory, and all writes to a volatile variable are written directly to main memory, there are still situations where it is not enough to declare a variable volatile


## Performance Considerations of volatile

Reading and writing of volatile variables causes the variable to be read or written to main memory. Reading from and writing to main memory is more expensive than accessing the CPU cache. Accessing volatile variables also prevent instruction reordering which is a normal performance enhancement technique. Thus, you should only use volatile variables when you really need to enforce visibility of variables. 
