---
layout: posts
title: Java Concurrent Column 2
tags:
- java
- concurrent
date: 2020-03-15
---

# This is the second half about Java Concurrent of my blog

## non-blocking synchronization
- Much of the recent research on concurrent algorithms has focused on nonblock- ing algorithms, which use low-level atomic machine instructions such as compare- and-swap instead of locks to ensure data integrity under concurrent access. Non- blocking algorithms are used extensively in operating systems and JVMs for thread and process scheduling, garbage collection, and to implement locks and other concurrent data structures.
- Nonblocking algorithms are considerably more complicated to design and im- plement than lock-based alternatives, but they can **offer significant scalability and liveness advantages**. They coordinate at a finer level of granularity and can greatly reduce scheduling overhead because they don’t block when multiple threads contend for the same data. Further, they are `immune to deadlock and other liveness problems`. In lock-based algorithms, other threads cannot make progress if a thread goes to sleep or spins while holding a lock, whereas `nonblocking algorithms are impervious to individual thread failures`. As of Java 5.0, it is possible to build efficient **nonblocking algorithms in Java using the atomic variable classes such as AtomicInteger and AtomicReference**.
- Atomic variables can also be used as **“better volatile variables”** even if you are not developing nonblocking algorithms. `Atomic variables offer the same memory semantics as volatile variables`, but with additional support for atomic updates— making them ideal for counters, sequence generators, and statistics gathering while offering better scalability than lock-based alternatives.
- Coordinating access to shared state using a consistent locking protocol ensures that whichever thread holds the lock guarding a set of variables has exclusive access to those variables, and that any changes made to those variables are visible to other threads that subsequently acquire the lock.
- `Volatile variables are a lighter-weight synchronization mechanism` than locking `because they do not involve context switches or thread scheduling`. However, volatile variables have some limitations compared to locking: while they provide similar visibility guarantees, they `cannot be used to construct atomic compound actions`. This means that volatile variables cannot be used when one variable de- pends on another, or when the new value of a variable depends on its old value. This limits when volatile variables are appropriate, since they cannot be used to reliably implement common tools such as counters or mutexes.
- This can be a serious problem **if the blocked thread is a high-priority thread but the thread holding the lock is a lower-priority thread—a performance hazard known as priority inversion**. Even though the higher-priority thread should have precedence, it must wait until the lock is released, and this effectively down- grades its priority to that of the lower-priority thread. If a thread holding a lock is permanently blocked (due to an infinite loop, deadlock, livelock, or other liveness failure), any threads waiting for that lock can never make progress.

# hardware
- `Exclusive locking is a pessimistic technique`—it assumes the worst (if you don’t lock your door, gremlins will come in and rearrange your stuff) and doesn’t proceed until you can guarantee, by acquiring the appropriate locks, that other threads will not interfere.
- For fine-grained operations, there is an alternate approach that is often more efficient—`the optimistic approach`, whereby you proceed with an update, hopeful that you can complete it without interference. `This approach relies on collision detection to determine if there has been interference from other parties during the update`, in which case the operation fails and can be retried (or not). The optimistic approach is like the old saying, `“It is easier to obtain forgiveness than permission”`, where “easier” here means “more efficient”.
- Processors designed for multiprocessor operation provide special instructions for managing concurrent access to shared variables. Early processors had atomic **test-and-set, fetch-and-increment, or swap** instructions sufficient for implementing mutexes that could in turn be used to implement more sophisticated concurrent objects. Today, nearly every modern processor has some form of atomic read- modify-write instruction, such as **compare-and-swap or load-linked/store-conditional**. Operating systems and JVMs use these instructions to implement locks and con- current data structures, but until Java 5.0 they had not been available directly to Java classes.

# Compare and swap
- The approach taken by most processor architectures, including IA32 and Sparc, is to implement a **compare-and-swap (CAS)** instruction. (Other processors, such as PowerPC, implement the same functionality with a pair of instructions: load- linked and store-conditional.) `CAS has three operands—a memory location V on which to operate, the expected old value A, and the new value B. CAS atomically updates V to the new value B, but only if the value in V matches the expected old value A; otherwise it does nothing`. In either case, it returns the value currently in V. (The `variant called compare-and-set instead returns whether the operation succeeded`.) **CAS means “I think V should have the value A; if it does, put B there, otherwise don’t change it but tell me I was wrong.” CAS is an optimistic technique**—`it proceeds with the update in the hope of success`, and can detect failure if another thread has updated the variable since it was last examined. SimulatedCAS in Listing 15.1 illustrates the semantics (but not the implementation or performance) of CAS.
- `When multiple threads attempt to update the same variable simultaneously using CAS, one wins and updates the variable’s value, and the rest lose`. But the losers are not punished by suspension, as they could be if they failed to acquire a lock; instead, they are told that they didn’t win the race this time but can try again. Because a thread that loses a CAS is not blocked, it can decide whether it wants to try again, take some other recovery action, or do nothing.3 This flexibility eliminates many of the liveness hazards associated with locking (though in unusual cases can introduce the risk of livelock—see Section 10.3.3).
- CAS addresses the problem of **implementing atomic read-modify-write sequences without locking**, `because it can detect interference from other threads`.

## counter implemented by CAS
- At first glance, the CAS-based counter looks as if it should perform worse than a lock-based counter; it has more operations and a more complicated control flow, and depends on the seemingly complicated CAS operation. But in reality, CAS-based counters significantly outperform lock-based counters if there is even a small amount of contention, and often even if there is no contention. The fast path for uncontended lock acquisition typically requires at least one CAS plus other lock-related housekeeping, so more work is going on in the best case for a lock-based counter than in the normal case for the CAS-based counter. Since the CAS succeeds most of the time (assuming low to moderate contention), the hardware will correctly predict the branch implicit in the while loop, minimizing the overhead of the more complicated control logic.
- The language syntax for locking may be compact, but the work done by the JVM and OS to manage locks is not. Locking entails traversing a relatively com- plicated code path in the JVM and may entail OS-level locking, thread suspension, and context switches. In the best case, locking requires at least one CAS, so using locks moves the CAS out of sight but doesn’t save any actual execution cost. On the other hand, executing a CAS from within the program involves no JVM code, system calls, or scheduling activity. What looks like a longer code path at the ap- plication level is in fact a much shorter code path when JVM and OS activity are taken into account. `The primary disadvantage of CAS is that it forces the caller to deal with contention (by retrying, backing off, or giving up), whereas locks deal with contention automatically by blocking until the lock is available`.
- Competitive forces will likely result in continued CAS performance improvement over the next sev- eral years. A good rule of thumb is that the **cost of the “fast path” for uncontended lock acquisition and release on most processors is approximately twice the cost of a CAS**.

## CAS support in JVM
- So, how does Java code convince the processor to execute a CAS on its behalf? Prior to Java 5.0, there was no way to do this short of writing native code. `In Java 5.0, low-level support was added to expose CAS operations on int, long, and object references`, and the `JVM compiles these into the most efficient means provided by the underlying hardware`. On platforms supporting CAS, the run- time inlines them into the appropriate machine instruction(s); `in the worst case, if a CAS-like instruction is not available the JVM uses a spin lock`. This low-level JVM support is used by the atomic variable classes (AtomicXxx in java.util.con- current.atomic) to provide an efficient CAS operation on numeric and reference types; these atomic variable classes are used, directly or indirectly, to implement most of the classes in java.util.concurrent.

# Other liveness hazards
- While deadlock is the most widely encountered liveness hazard, there are sev- eral other liveness hazards you may encounter in concurrent programs including starvation, missed signals, and livelock.


## Starvation
- Starvation occurs when a thread is perpetually denied access to resources it needs in order to make progress; the most commonly starved resource is CPU cycles. Starvation in Java applications can be caused by inappropriate use of thread prior- ities. It can also be caused by executing nonterminating constructs (infinite loops or resource waits that do not terminate) with a lock held, since other threads that need that lock will never be able to acquire it.
- The thread priorities defined in the Thread API are merely scheduling hints. The Thread API defines ten priority levels that the JVM can map to operating system scheduling priorities as it sees fit. This mapping is platform-specific, so two Java priorities can map to the same OS priority on one system and different OS priorities on another.
- **Avoid the temptation to use thread priorities, since they increase platform dependence and can cause liveness problems**. Most concurrent applica- tions can use the default priority for all threads.


## Poor responsiveness
- One step removed from starvation is poor responsiveness, which is not uncom- mon in GUI applications using background threads.
- If the work done by other threads are truly background tasks, lowering their priority can make the foreground tasks more responsive.

## Livelock
- **Livelock is a form of liveness failure** in which a thread, while **not blocked**, still **cannot make progress** because it keeps retrying an operation that **will always fail**. 
- Livelock often occurs in transactional messaging applications, where the messaging infrastructure rolls back a transaction if a message cannot be processed successfully, and puts it back at the head of the queue. If a bug in the message handler for a particular type of message causes it to fail, **every time the message is dequeued and passed to the buggy handler, the transaction is rolled back**. Since the message is now back at the head of the queue, the **handler is called over and over with the same result**. (This is sometimes called the **poison message** problem.) The **message handling thread is not blocked, but it will never make progress either**. This form of livelock often comes from **overeager error-recovery code that mistakenly treats an unrecoverable error as a recoverable one**.
- This is similar to what happens when **two overly polite people** are walking in opposite directions in a hallway: each steps out of the other’s way, and now they are again in each other’s way. So they both step aside again, and again, and again. . .

### Solutions
- The solution for this variety of livelock is **to introduce some randomness into the retry mechanism**. For example, when two stations in an ethernet network try to send a packet on the shared carrier at the same time, the packets collide. The stations detect the collision, and each tries to send their packet again later. If they each retry exactly one second later, they collide over and over, and neither packet ever goes out, even if there is plenty of available bandwidth. To avoid this, we make each wait an amount of time that includes a random component. (The ethernet protocol also includes exponential backoff after repeated collisions, reducing both congestion and the risk of repeated failure with multiple colliding stations.) Retrying with random waits and backoffs can be equally effective for avoiding livelock in concurrent applications.

### Summary
- Liveness failures are a serious problem because there is no way to recover from them short of aborting the application. The most common form of liveness failure is lock-ordering deadlock. Avoiding lock ordering deadlock starts at design time: ensure that when threads acquire multiple locks, they do so in a consistent order. The best way to do this is by using open calls throughout your program. This greatly reduces the number of places where multiple locks are held at once, and makes it more obvious where those places are.
# Reference 


# Performance
- One of the primary reasons to use threads is to improve performance.
- First make your program right, then make it fast—and then only if your performance requirements and measurements tell you it needs to be faster. In designing a con- current application, squeezing out the last bit of performance is often the least of your concerns.
- When the performance of an activity is limited by availability of a par- ticular resource, we say it is bound by that resource: CPU-bound, database-bound, etc.
- using multiple threads always introduces some performance costs compared to the single-threaded approach. These include the overhead associated with coordinating between threads (locking, signaling, and memory synchronization), increased context switching,thread creation and teardown, and scheduling overhead. When threading is employed effectively, these costs are more than made up for by greater throughput, responsiveness, or capacity. On the other hand, a poorly designed concurrent application can perform even worse than a comparable sequential one.
- we want to keep the CPUs busy with **useful** work

## Scalability
- Scalability describes the ability to improve throughput or capacity when additional computing resources (such as additional CPUs, memory, stor- age, or I/O bandwidth) are added.
- Nearly all engineering decisions involve some form of tradeoff. 
- This is one of the reasons why most optimizations are premature: **they are often undertaken before a clear set of requirements is available**.
- Avoid premature optimization. **First make it right, then make it fast**—if it is not already fast enough.
- Measure, don’t guess.

### Amdahl's law
-  the theoretical speedup is always limited by the part of the task that cannot benefit from the improvement.
-   If F is the fraction of the calculation that must be executed serially, then Amdahl’s law says that on a machine with N processors, we can achieve a speedup of at most:
Speedup ≤ 1 / (F + (1 − F)/N)
- As N approaches infinity, the maximum speedup converges to 1/F, meaning that **a program in which fifty percent of the processing must be executed serially can be sped up only by a factor of two**, regardless of how many processors are available, and a program in which ten percent must be executed serially can be sped up by at most a factor of ten. 
- Amdahl’s law also quantifies the efficiency cost of serialization. With ten processors, a program with 10% serialization can achieve at most a speedup of 5.3 (at 53% utilization), and with 100 processors it can achieve at most a speedup of 9.2 (at 9% utilization). It takes a lot of inefficiently utilized CPUs to never get to that factor of ten.
- It is clear that as processor counts increase, even a small percentage of serialized execution limits how much throughput can be increased with additional computing resources.
- All concurrent applications have some sources of serialization; if you think yours does not, look again.
- Amdahl’s law tells us that the scalability of an application is driven by the proportion of code that must be executed serially. Since the primary source of serialization in Java programs is the exclusive resource lock, scalability can often be improved by spending less time holding locks, either by reducing lock granu- larity, reducing the duration for which locks are held, or replacing exclusive locks with nonexclusive or nonblocking alternatives.

# Costs introduced by threads
## Context switching
- Context switches are not free; thread scheduling requires manipulating shared data structures in the OS and JVM. The OS and JVM use the same CPUs your pro- gram does; more CPU time spent in JVM and OS code means less is available for your program.
- When a new thread is switched in, the data it needs is unlikely to be in the local processor cache, so a context switch causes a flurry of cache misses, and thus threads run a little more slowly when they are first scheduled.
- The actual cost of context switching varies across platforms, but a good rule of thumb is that a **context switch costs the equivalent of 5,000 to 10,000 clock cycles**, or several microseconds on most current processors.

## memory synchronization
- The performance cost of synchronization comes from several sources. The visibility guarantees provided by synchronized and volatile may entail using **special instructions called memory barriers** that can flush or invalidate caches, flush hard- ware write buffers, and stall execution pipelines. **Memory barriers** may also have indirect performance consequences because they **inhibit other compiler optimizations**; most operations cannot be reordered with memory barriers.
- When assessing the performance impact of synchronization, it is **important to distinguish between contended and uncontended synchronization**. The synchronized mechanism is optimized for the uncontended case (**volatile is always uncontended**), and at this writing, the performance cost of **a “fast-path” uncontended synchronization ranges from 20 to 250 clock cycles** for most systems. While this is certainly not zero, the effect of needed, uncontended synchronization is rarely significant in overall application performance, and the alternative involves compromising safety and potentially signing yourself (or your succes- sor) up for some very painful bug hunting later.
- Modern **JVMs can reduce the cost of incidental synchronization** by optimizing away locking that can be proven never to contend. If a lock object is accessible only to the current thread, the JVM is permitted to optimize away a lock acquisi- tion because there is no way another thread could synchronize on the same lock. For example, the lock acquisition in following Listing can always be eliminated by the JVM.

Following synchronization has no effect
```java
synchronized (new Object()) {
    // do something
}
```

- More sophisticated JVMs can use **escape analysis** to identify when a local object reference is never published to the heap and is therefore thread-local. As below sample:
```java
public String getStoogeNames() {
List<String> stooges = new Vector<String>(); stooges.add("Moe");
stooges.add("Larry");
stooges.add("Curly");
return stooges.toString();
}
```
- the only reference to the List is the local variable stooges, and **stack-confined variables are automatically thread-local**. A naive execution of getStoogeNames would acquire and release the lock on the Vector four times, once for each call to add or toString. However, a smart runtime compiler can inline these calls and then see **that stooges and its internal state never escape**, and therefore that **all four lock acquisitions can be eliminated**.
- Even without escape analysis, compilers can also perform **lock coarsening**, the **merging of adjacent synchronized blocks using the same lock**. For getStooge- Names, a JVM that performs lock coarsening might combine the three calls to add and the call to toString into a single lock acquisition and release, using heuristics on the relative cost of synchronization versus the instructions inside the synch- ronized block.5 Not only does this reduce the synchronization overhead, but it also gives the optimizer a much larger block to work with, likely enabling other optimizations.

> Don’t worry excessively about the cost of uncontended synchronization. The basic mechanism is already quite fast, and JVMs can perform addi- tional optimizations that further reduce or eliminate the cost. Instead, focus optimization efforts on areas where lock contention actually occurs.

- Synchronization by one thread can also affect the performance of other threads. Synchronization creates traffic on the shared memory bus; this bus has a limited bandwidth and is shared across all processors. If threads must compete for synchronization bandwidth, all threads using synchronization will suffer.

## Blocking
- **Uncontended synchronization** can be handled **entirely within the JVM** (Bacon et al., 1998); **contended synchronization may require OS activity**, which adds to the cost. When locking is contended, the losing thread(s) must block. The JVM can implement blocking either via spin-waiting (repeatedly trying to acquire the lock until it succeeds) or by suspending the blocked thread through the operating system. Which is more efficient depends on the relationship between context switch overhead and the time until the lock becomes available; spin-waiting is preferable for short waits and suspension is preferable for long waits. Some JVMs choose between the two adaptively based on profiling data of past wait times, but most just suspend threads waiting for a lock.

## Reducing lock contention
- We’ve seen that **serialization hurts scalability** and that **context switches hurt performance**. **Contended locking causes both**, so **reducing lock contention can improve both performance and scalability**.
Access to resources guarded by an exclusive lock is serialized—only one thread at a time may access it. Of course, we use locks for good reasons, such as preventing data corruption, but this safety comes at a price. Persistent contention for a lock limits scalability.
- The principal threat to scalability in concurrent applications is the exclu- sive resource lock.
- Two factors influence the likelihood of contention for a lock: how often that lock is requested and how long it is held once acquired.7 If the product of these factors is sufficiently small, then most attempts to acquire the lock will be uncon- tended, and lock contention will not pose a significant scalability impediment.

### There are three ways to reduce lock contention:
- Reduce the duration for which locks are held;
- Reduce the frequency with which locks are requested; or
- Replace exclusive locks with coordination mechanisms that permit
greater concurrency.

## Narrowing lock scope
- **An effective way to reduce the likelihood of contention is to hold locks as briefly as possible**. This can be done by moving code that doesn’t require the lock out of synchronized blocks, especially for expensive operations and potentially block- ing operations such as I/O.
- It is easy to see how holding a “hot” lock for too long can limit scalability
- Reducing the scope of the lock in userLocationMatches substantially reduces the number of instructions that are executed with the lock held. **By Amdahl’s law, this removes an impediment to scalability because the amount of serialized code is reduced**.
- Because AttributeStore has only one state variable, attributes, we can im- prove it further by the technique of **delegating thread safety** (Section 4.3). By replacing attributes with a thread-safe Map (a Hashtable, synchronizedMap, or Con- currentHashMap), AttributeStore can delegate all its thread safety obligations to the underlying thread-safe collection.

## Reducing lock granularity
- The other way to reduce the fraction of time that a lock is held (and therefore the likelihood that it will be contended) is to **have threads ask for it less often**. This can be accomplished **by lock splitting and lock striping**, which involve **using separate locks to guard multiple independent state variables previously guarded by a single lock**. These techniques reduce the granularity at which locking occurs, potentially allowing greater scalability—but using more locks also increases the risk of deadlock.
- If a lock guards more than one **independent** state variable, you may be able to improve scalability by splitting it into multiple locks that each guard different variables. This results in each lock being requested less often.
- After splitting the lock, each new finer-grained lock will see less locking traffic than the original coarser lock would have.

## Lock stripping
- Splitting a heavily contended lock into two is likely to result in two heavily contended locks. 
- Lock splitting can sometimes be extended to partition locking on a variable- sized set of independent objects, in which case it is called lock striping. For exam- ple, the implementation of ConcurrentHashMap uses an array of 16 locks, each of which guards 1/16 of the hash buckets; bucket N is guarded by lock N mod 16.
- One of the downsides of lock striping is that locking the collection for ex- clusive access is more difficult and costly than with a single lock. Usually **an operation can be performed by acquiring at most one lock**, but **occasionally you need to lock the entire collection**, as when ConcurrentHashMap needs **to expand the map and rehash the values** into a larger set of buckets. This is typically done by acquiring all of the locks in the stripe set
- common optimizations such as caching frequently computed values can introduce “hot fields” that limit scalability.
- A common optimization is to update a separate counter as entries are added or removed; this slightly increases the cost of a put or remove operation to keep the counter up-to-date, but reduces the cost of the size operation from O(n) to O(1).
- In this case, the counter is called a **hot field** because every mutative operation needs to access it.
- ConcurrentHashMap avoids this problem by having size enumerate the stripes and add up the number of elements in each stripe, instead of maintaining a global count. To avoid enumerating every element, ConcurrentHashMap maintains a separate count field for each stripe, also guarded by the stripe lock.

## Alternative to exclusive lock
- A third technique for mitigating the effect of lock contention **is to forego the use of exclusive locks** in favor of a more concurrency-friendly means of managing shared state. These include **using the concurrent collections, read-write locks, immutable objects and atomic variables**.

### ReadWriteLock 
- enforces a **multiple-reader, single-writer** locking discipline: more than one reader can access the shared resource concurrently so long as none of them wants to modify it, but writers must acquire the lock excusively. For read-mostly data structures, ReadWriteLock can offer greater concurrency than exclusive locking; **for read-only data structures, immutability can eliminate the need for locking entirely**.
- Atomic variables (see Chapter 15) offer a means of reducing the cost of updat- ing “hot fields” such as statistics counters, sequence generators, or the reference
- If size is called frequently compared to mutative operations, striped data structures can optimize for this by caching the collection size in a volatile whenever size is called and invalidating the cache (setting it to -1) whenever the collection is modified. If the cached value is nonnegative on entry to size, it is accurate and can be returned; otherwise it is recomputed.
- The atomic variable classes pro- vide very fine-grained (and therefore more scalable) atomic operations on integers or object references, and are implemented using low-level concurrency primitives (such as compare-and-swap) provided by most modern processors. If your class has a small number of hot fields that do not participate in invariants with other variables, replacing them with atomic variables may improve scalability.

# Comparing Map
- The single-threaded performance of ConcurrentHashMap is slightly better than that of a synchronized HashMap, but it is in concurrent use that it really shines. The implementation of ConcurrentHashMap assumes the most common operation is retrieving a value that already exists, and is therefore optimized to **provide highest performance and concurrency for successful get operations**.
- The major scalability impediment for the synchronized Map implementations is that there is a single lock for the entire map, so only one thread can access the map at a time. On the other hand, ConcurrentHashMap does no locking for most successful read operations, and **uses lock striping for write operations** and those few read operations that do require locking. As a result, multiple threads can access the Map concurrently without blocking.
- The numbers for the synchronized collections are not as encouraging. Perfor- mance for the one-thread case is comparable to ConcurrentHashMap, but once the load transitions from mostly uncontended to mostly contended—which happens here at two threads—the synchronized collections suffer badly. This is common behavior for code whose scalability is limited by lock contention. So long as contention is low, time per operation is dominated by the time to actually do the work and throughput may improve as threads are added. Once contention becomes significant, time per operation is dominated by context switch and scheduling delays, and adding more threads has little effect on throughput.

# Building a asynchronous log
- Building a logger that moves the I/O to another thread may improve performance, but it also introduces a number of design complications, such as interruption (what happens if a thread blocked in a logging operation is interrupted?), service guarantees (does the logger guarantee that a success- fully queued log message will be logged prior to service shutdown?), saturation policy (what happens when the producers log messages faster than the logger thread can handle them?), and service lifecycle (how do we shut down the logger, and how do we communicate the service state to producers?).

# Reducing context switching
- The “get in, get out” principle of Section 11.4.1 tells us that **we should hold locks as briefly as possible**, because **the longer a lock is held, the more likely that lock will be contended**. If a thread blocks waiting for I/O while holding a lock, another thread is more likely to want the lock while the first thread is holding it. Concurrent systems perform much better when most lock acquisitions are uncontended, because contended lock acquisition means more context switches. A coding style that encourages more context switches thus yields lower overall throughput.

# Testing concurrency
- we defined safety as “nothing bad ever happens” and liveness as “something good eventually happens”.
- when interrupted, it throws InterruptedException. This is one of the few cases in which it is appropriate to subclass Thread explicitly instead of using a Runnable in a pool: in order to test proper termination with join.
- The result of **Thread.getState should not be used** for concurrency control, and is of limited usefulness for testing—its primary utility is as a source of debugging information.
- a common error in implementing semaphore-controlled buffers is to forget that the code actually doing the insertion and extraction requires mutual exclu- sion (using synchronized or ReentrantLock). A sample run of PutTakeTest with a version of BoundedBuffer that omits making doInsert and doExtract synch- ronized fails fairly quickly. 
- **Tests should be run on multiprocessor systems to increase the diversity of potential interleavings. However, having more than a few CPUs does not necessarily make tests more effective. To maximize the chance of detecting timing-sensitive data races, there should be more active threads than CPUs, so that at any given time some threads are running and some are switched out, thus reducing the predicatability of interactions between threads**.
- Tests like PutTakeTest tend to be good at finding safety violations. For exam- ple, a common error in implementing semaphore-controlled buffers is to forget that the code actually doing the insertion and extraction requires mutual exclu- sion (using synchronized or ReentrantLock). A sample run of PutTakeTest with a version of BoundedBuffer that omits making doInsert and doExtract synch- ronized fails fairly quickly. Running PutTakeTest with a few dozen threads iterating a few million times on buffers of various capacity on various systems increases our confidence about the lack of data corruption in put and take.
- The source code **PutTakeTest.java** demonstreated aforesaid logic.

## Test resource management
- **The tests so far have been concerned with a class’s adherence to its specifica- tion—that it does what it is supposed to do. A secondary aspect to test is that it does not do things it is not supposed to do**, such as leak resources. Any object that holds or manages other objects should not continue to maintain references to those objects longer than necessary. Such storage leaks prevent garbage collectors from reclaiming memory (or threads, file handles, sockets, database connections, or other limited resources) and can lead to resource exhaustion and application failure.
