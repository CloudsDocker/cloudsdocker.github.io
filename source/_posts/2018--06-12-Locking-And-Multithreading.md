---
title: Locking and multithreading
tags:
- CAS
- Concurrent
---

# Single Writer principle

There is a lot of research in computer science for managing this contention that boils down to 2 basic approaches.  One is to provide mutual exclusion to the contended resource while the mutation takes place; the other is to take an optimistic strategy and swap in the changes if the underlying resource has not changed while you created the new copy.  


 
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


## Priority Inversion

Example of a priority inversion
Consider two tasks H and L, of high and low priority respectively, either of which can acquire exclusive use of a shared resource R. If H attempts to acquire R after L has acquired it, then H becomes blocked until L relinquishes the resource. Sharing an exclusive-use resource (R in this case) in a well-designed system typically involves L relinquishing R promptly so that H (a higher priority task) does not stay blocked for excessive periods of time. Despite good design, however, it is possible that a third task M of medium priority (p(L) < p(M) < p(H), where p(x) represents the priority for task (x)) becomes runnable during L's use of R. At this point, M being higher in priority than L, preempts L, causing L to not be able to relinquish R promptly, in turn causing H—the highest priority process—to be unable to run. This is called priority inversion where a higher priority task is preempted by a lower priority one.



## RCU
In computer science, read-copy-update (RCU) is a synchronization mechanism based on mutual exclusion.[note 1] It is used when performance of reads is crucial and is an example of space–time tradeoff, enabling fast operations at the cost of more space.


