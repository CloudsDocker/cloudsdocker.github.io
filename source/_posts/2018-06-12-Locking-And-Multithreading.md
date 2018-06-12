---
title: Locking and multithreading
tags:
- CAS
- Concurrent
---

# Single Writer principle

There is a lot of research in computer science for managing this contention that boils down to 2 basic approaches.  One is to provide mutual exclusion to the contended resource while the mutation takes place; the other is to take an optimistic strategy and swap in the changes if the underlying resource has not changed while you created the new copy.  

# Memory Barier

Memory barriers, or fences, are a set of processor instructions used to apply ordering limitations on memory operations. 


The keyword volatile prevents this problem because it establishes a happens before relationship between the write to the turn variable and the write to the intentFirst variable. The compiler cannot re-order these write operations and if necessary it must forbid the processor from doing so with a memory barrier.


A memory barrier, also known as a membar, memory fence or fence instruction, is a type of barrier instruction that causes a central processing unit (CPU) or compiler to enforce an ordering constraint on memory operations issued before and after the barrier instruction. This typically means that operations issued prior to the barrier are guaranteed to be performed before operations issued after the barrier.

Memory barriers are necessary because most modern CPUs employ performance optimizations that can result in out-of-order execution. This reordering of memory operations (loads and stores) normally goes unnoticed within a single thread of execution, but can cause unpredictable behaviour in concurrent programs and device drivers unless carefully controlled.


# Non blocking programing
Implementation
With few exceptions, non-blocking algorithms use atomic read-modify-write primitives that the hardware must provide, the most notable of which is compare and swap (CAS).

 
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

This operation is used to implement synchronization primitives like semaphores and mutexes,[1] as well as more sophisticated lock-free and wait-free algorithms.

Algorithms built around CAS typically read some key memory location and remember the old value. Based on that old value, they compute some new value. Then they try to swap in the new value using CAS, where the comparison checks for the location still being equal to the old value. If CAS indicates that the attempt has failed, it has to be repeated from the beginning: the location is re-read, a new value is re-computed and the CAS is tried again.


A common workaround is to add extra "tag" or "stamp" bits to the quantity being considered. For example, an algorithm using compare and swap on a pointer might use the low bits of the address to indicate how many times the pointer has been successfully modified. Because of this, the next compare-and-swap will fail, even if the addresses are the same, because the tag bits will not match. This does not completely solve the problem, as the tag bits will eventually wrap around, but helps to avoid it. Some architectures provide a double-word compare and swap, which allows for a larger tag. This is sometimes called ABAʹ since the second A is made slightly different from the first. Such tagged state references are also used in transactional memory.


## Priority Inversion

Example of a priority inversion
Consider two tasks H and L, of high and low priority respectively, either of which can acquire exclusive use of a shared resource R. If H attempts to acquire R after L has acquired it, then H becomes blocked until L relinquishes the resource. Sharing an exclusive-use resource (R in this case) in a well-designed system typically involves L relinquishing R promptly so that H (a higher priority task) does not stay blocked for excessive periods of time. Despite good design, however, it is possible that a third task M of medium priority (p(L) < p(M) < p(H), where p(x) represents the priority for task (x)) becomes runnable during L's use of R. At this point, M being higher in priority than L, preempts L, causing L to not be able to relinquish R promptly, in turn causing H—the highest priority process—to be unable to run. This is called priority inversion where a higher priority task is preempted by a lower priority one.



## RCU
In computer science, read-copy-update (RCU) is a synchronization mechanism based on mutual exclusion.[note 1] It is used when performance of reads is crucial and is an example of space–time tradeoff, enabling fast operations at the cost of more space.

Read-copy-update allows multiple threads to efficiently read from shared memory by deferring updates after pre-existing reads to a later time while simultaneously marking the data, ensuring new readers will read the updated data. This makes all readers proceed as if there were no synchronization involved, hence they will be fast, but also making updates more difficult.


