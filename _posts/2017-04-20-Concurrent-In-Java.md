---
layout: posts
title: Java Concurrent
tags:
- Java
- Concurrent
date: 2020-03-10
---
# This blog is about noteworthy pivot points about Java Concurrent Framework
> Back to Java old days there were wait()/notify() which is error prone, while from Java 5.0 there was Concurrent framework being introduced, this page list some pivot points.

# CountDownLatch
- CountDownLatch in Java is a kind of synchronizer which allows one Thread  to wait for one or more Threads before starts processing. 
- You can also implement same functionality using  wait and notify mechanism in Java but it requires lot of code and getting it write in first attempt is tricky,  With CountDownLatch it can  be done in just few lines.
-  One of the **disadvantage** of CountDownLatch is that its **not reusable once count reaches to zero** you can not use CountDownLatch any more, but don't worry Java concurrency API has another concurrent utility called CyclicBarrier for such requirements.
## When to use CountDownLatch
Classical example of using CountDownLatch in Java  is any server side core Java application which uses services architecture,  where multiple services is provided by multiple threads and application can not start processing  until all services have started successfully as shown in our CountDownLatch example.

## Summary
- Main Thread wait on Latch by calling CountDownLatch.await() method while other thread calls CountDownLatch.countDown() to inform that they have completed.


# CyclicBarrier
- there is different you can not reuse CountDownLatch once the count reaches zero while you can **reuse CyclicBarrier** by calling **reset()** method which resets Barrier to its initial State. What it implies that **CountDownLatch is a good for one-time** events like **application start-up time** and **CyclicBarrier can be used to in case of the recurrent event** e.g. concurrently calculating a solution of the big problem etc.
- a simple example of CyclicBarrier in Java on which we initialize CyclicBarrier with 3 parties, means **in order to cross barrier, 3 thread needs to call await() method**. each **thread calls await method** in short duration but they **don't proceed until all 3 threads reached the barrier**, once **all thread reach the barrier**, barrier gets broker and **each thread started their execution** from that point. 
- Sample can be found at **CyclicBarrierDemo.java**
## Use cases:
- To implement multi player game which can not begin until all player has joined.
- Perform lenghty calculation by breaking it into smaller individual tasks. In general, to implement Map-Reduce technique.
- CyclicBarrier can perform a completion task once all thread reaches to the barrier, This can be provided while creating CyclicBarrier.
- If CyclicBarrier is initialized with 3 parties means 3 thread needs to call await method to break the barrier.
- The thread will block on await() until all parties reach to the barrier, another thread interrupt or await timed out.
- CyclicBarrier.reset() put Barrier on its initial state, other thread which is waiting or not yet reached barrier will terminate with java.util.concurrent.BrokenBarrierException.


# ThreadLocal
- ThreadLocal in Java is another way to achieve thread-safety **apart from writing immutable** classes.
- ThreadLocal in Java is a different way to achieve thread-safety, it doesn't address synchronization requirement, instead it eliminates sharing by providing explicitly copy of Object to each thread.
- Since Object is no more shared there is no requirement of Synchronization which can improve scalability and performance of application.
- One of the classic example of ThreadLocal is sharing SimpleDateForamt. Since SimpleDateFormat is not thread safe, having a global formatter may not work but having per Thread formatter will certainly work. but it can **be source of severe memory leak** and java.lang.OutOfMemoryError if not used carefully. so avoid until you don't have any other option.


# Semaphone
- Semaphore provides two main method acquire() and release() for getting permits and releasing permits. acquire() method blocks until permit is available.
-  Semaphore provides both blocking method as well as unblocking method to acquire permits. This Java concurrency tutorial focus on a very simple example of Binary Semaphore and demonstrate how mutual exclusion can be achieved using Semaphore in Java.
## Binary Semaphone
a Counting semaphore with **one permit is known as binary semaphore** because it has only two state permit available or permit unavailable. Binary semaphore can be used to implement mutual exclusion or critical section where only one thread is allowed to execute. Thread will wait on acquire() until Thread inside critical section release permit by calling release() on semaphore.

## Scenarios usage
1) To implement better Database connection pool which will block if no more connection is available instead of failing and handover Connection as soon as its available.
2) To put a bound on collection classes. by using semaphore you can implement bounded collection whose bound is specified by counting semaphore.
3)  That's all on Counting semaphore example in Java. Semaphore is real nice concurrent utility which can greatly simply design and implementation of bounded resource pool. Java 5 has added several useful  concurrent utility and deserve a better attention than casual look.


# Race condition
- Race conditions occurs when two thread operate on same object without proper synchronization and there operation interleaves on each other. Classical example of Race condition is incrementing a counter since increment is not an atomic operation and can be further divided into three steps like read, update and write. if two threads tries to increment count at same time and if they read same value because of interleaving of read operation of one thread to update operation of another thread, one count will be lost when one thread overwrite increment done by other thread.
- I found that two code patterns namely **"check and act"** and **"read modify write"** can **suffer race condition** if not synchronized properly. 
   - classical example of "check and act" race condition in Java is getInstance() method of Singleton Class,
   - put if absent scenario. consider below code

if(!hashtable.contains(key)){

hashtable.put(key,value);

}
## Fix race condition:
-In order to fix this race condition in Java you need to wrap this code **inside synchronized block** which makes them atomic together because no thread can go inside synchronized block if one thread is already there.
- **IllegalMonitorStateException in Java which will occur** if we don't call wait (), notify () or notifyAll () method from synchronized context.
- Any potential race condition between wait and notify method in Java

# Thread in Java
## details:
- A thread is essentialy a subdivision of a process, or LWP: lightweight process.
- Crucially, each process has its own memory space. 
- A thread is a subdivision that shares the memory space of its parent process. 
- Threads belonging to a process usually share a few other key resources as well, such as their working directory, environment variables, file handles etc.
- On the other hand, each thread has its **own private stack and registers, including program counter**.  program counter (PC) register keeps track of the current instruction executing at any moment. That is like a pointer to the current instruction in sequence of instructions in a program. 
- Method area: In general, method area is a logical part of heap area. But that is left to the JVM implementers to decide.  Method area has per class structures and fields. Nothing but static fields and structures.
- Depending on the OS, threads may have some other private resources too, such as **thread-local storage** (effectively, a way of referring to "variable number X", where each thread has its own private value of X).


## Wait & Notify
- Since wait method is **not defined in Thread** class, you cannot simply call Thread.wait(), that won't work but since many Java developers are used to calling Thread.sleep() they try the same thing with wait() method and stuck.
- You need to call **wait() method on the object** which is **shared between two threads**, in producer-consumer problem its the queue which is shared between producer and consumer threads.
```java
synchronized(lock){
	while(!someCondition){
		lock.wait();
	}
}
```

## Tips
- **Always call wait(), notify() and notifyAll() methods from synchronized method or synchronized block** otherwise JVM will **throw IllegalMonitorStateException**.
- Always call wait and notify method **from a loop** and **never from if()** block, because loop test waiting condition before and after sleeping and handles notification even if waiting for the condition is not changed.
- Always **call wait in shared object** e.g. shared queue in this example.
- Prefer **notifyAll() over notify()** method due to reasons given in this article. 

## Fork-Join
- Fork/join tasks is “pure” in-memory algorithms in which no I/O operations come into picture.it is based on a **work-stealing algorithm**. 
- Java’s most attractive part is it makes things easier and easier.
- its really challenging where several threads are working together to accomplish a large task so again java has tried to make things easy and simplifies this concurrency using Executors and Thread Queue.
- it work on **divide and conquer algorithm** and **create sub-tasks and communicate with each other to complete**.
- New fork-join executor framework has been created which is responsible for creating one new task object which is again responsible for creating new sub-task object and waiting for sub-task to be completed.internally it maintains a thread pool and executor assign pending task to this thread pool to complete when one task is waiting for another task to complete. whole Idea of fork-join framework is to leverage multiple processors of advanced machine.

## Thread.yield()
- This static method is essentially used to notify the system that the current thread is willing to "give up the CPU" for a while. The general idea is that: The thread scheduler will select a different thread to run instead of the current one. However, the details of how yielding is implemented by the thread scheduler differ from platform to platform. In general, you shouldn't rely on it behaving in a particular way. Things that differ include:
   - when, after yielding, the thread will get an opportunity to run again;
   - whether or not the thread foregoes its remaining quantum.

### Windows
- In the Hotspot implementation, the way that Thread.yield() works has changed between Java 5 and Java 6.
- In **Java 5, Thread.yield() calls the Windows API call Sleep(0)**. This has the special effect of clearing the current thread's quantum and putting it to the end of the queue for its priority level. In other words, all runnable threads of the same priority (and those of greater priority) will get a chance to run before the yielded thread is next given CPU time. When it is eventually re-scheduled, it will come back with a full quantum, but doesn't "carry over" any of the remaining quantum from the time of yielding. This behaviour is a little different from a non-zero sleep where the sleeping thread generally loses 1 quantum value (in effect, 1/3 of a 10 or 15ms tick).
- In **Java 6, this behaviour was changed. The Hotspot VM now implements Thread.yield() using the Windows SwitchToThread() API call**. This call makes the current thread give up its current timeslice, but not its entire quantum. This means that depending on the priorities of other threads, the yielding thread can be scheduled back in one interrupt period later. 

### Linux
- Under Linux, Hotspot simply calls sched_yield(). The consequences of this call are a little different, and possibly more severe than under Windows:
    - a yielded thread will not get another slice of CPU until all other threads have had a slice of CPU;
    - (at least in kernel 2.6.8 onwards), the fact that the thread has yielded is **implicitly taken into account by the scheduler's heuristics on its recent CPU allocation** — thus, implicitly, a thread that has yielded could be given more CPU when scheduled in the future.

### When to use yield()?
- I would say **practically never**. Its behaviour isn't standardly defined and there are generally better ways to perform the tasks that you might want to perform with yield():
- if you're trying to use only a portion of the CPU, you can do this in a more controllable way by estimating how much CPU the thread has used in its last chunk of processing, then **sleeping for some amount of time to compensate: see the sleep() method**;
- if you're **waiting for a process or resource to complete or become available, there are more efficient ways to accomplish this, such as by using join() to wait** for another thread to complete, using the wait/notify mechanism to allow one thread to signal to another that a task is complete, or ideally by using one of the Java 5 concurrency constructs such as a Semaphore or blocking queue.

## Thread Scheduling
- **thread scheduler**, part of the OS (usually) that is responsible for sharing the available CPUs out between the various threads. How exactly the scheduler works depends on the individual platform, but various modern operating systems (notably Windows and Linux) use largely similar techniques that we'll describe here.
- Note that we'll continue to talk about a single thread scheduler. On multiprocessor systems, there is generally some kind of scheduler per processor, which then need to be coordinated in some way. 
- Across platforms, thread scheduling tends to be based on at least the following criteria:
   - a **priority**, or in fact usually multiple "priority" settings that we'll discuss below;
   - a **quantum, or number of allocated timeslices of CPU**, which essentially determines the amount of CPU time a thread is allotted before it is forced to yield the CPU to another thread of the same or lower priority (the system will keep track of the remaining quantum at any given time, plus its default quantum, which could depend on thread type and/or system configuration);
   - a **state**, notably "runnable" vs "waiting";
   - **metrics** about the behaviour of threads, such as recent CPU usage or the time since it last ran (i.e. had a share of CPU), or the fact that it has "just received an event it was waiting for".
- Most systems use what we might dub **priority-based round-robin scheduling** to some extent. The general principles are:
   - a thread of **higher priority** (which is a function of base and local priorities) will **preempt** a thread of lower priority;
   - otherwise, threads of equal priority will essentially **take turns** at getting an allocated slice or quantum of CPU;
   - there are a few extra "tweaks" to make things work.

### States

Depending on the system, there are various states that a thread can be in. Probably the two most interesting are:
- **runnable**, which essentially means "ready to consume CPU"; being runnable is generally the minimum requirement for a thread to actually be scheduled on to a CPU;
- **waiting**, meaning that the thread currently cannot continue as it is waiting for a resource such as a lock or I/O, for memory to be paged in, for a signal from another thread, or simply for a period of time to elapse (sleep).

Other states include **terminated**, which means the thread's code has finished running but not all of the thread's resources have been cleared up, and a **new** state, in which the thread has been created, but not all resources necessary for it to be runnable have been created. 

### Quanta and clock ticks
- Each thread has a quantum, which is effectively how long it is allowed to keep hold of the CPU if:
   - it remains runnable;
   - the scheduler determines that no other thread needs to run on that CPU instead.
- Thread quanta are generally defined in terms of some number of **clock ticks**. If it doesn't otherwise cease to be runnable, the scheduler decides whether to preempt the currently running thread every clock tick. As a rough guide:
   - a clock tick is typically 10-15 ms under Windows; under Linux, it is 1ms (kernel 2.6.8 onwards);
   - a quantum is usually a small number of clock ticks, depending on the OS:
either 2, 6 or 12 clock ticks on Windows, depending on whether Windows is running in "server" mode:

Windows mode   | Foreground process | Non-foreground process
---|---|---
Normal|  6 ticks |2 ticks
Server | 12 ticks | 12 ticks

between 10-200 clock ticks (i.e. 10-200 ms) under Linux, though some granularity is introduced in the calculation— see below.
a thread is usually allowed to "save up" unused quantum, up to some limit and granularity.
- In Windows, a thread's quantum allocation is fairly stable. In Linux, on the other hand, a thread's quantum is dynamically adjusted when it is scheduled, depending partly on heuristics about its recent resource usage and partly on a nice value

#### Switching and scheduling algorithms

- At key moments, the thread scheduler considers whether to switch the thread that is currently running on a CPU. These key moments are usually:
   - **periodically**, via an interrupt routine, the scheduler will consider whether the currently running thread on each CPU has reached the end of its allotted **quantum**;
   - at any time, a currently running thread could **cease to be runnable** (e.g. by needing to wait, reaching the end of its execution or being forcibly killed);
   - when some other attribute of the thread changes (e.g. its priority or processor affinity4) which means that which threads are running needs to be re-assessed.
- At these decision points, the scheduler's job is essentially to decide, of all the **runnable** threads, **which are the most appropriate to actually be running on the available CPUs**. Potentially, this is quite a complex task. But we don't want the scheduler to waste too much time deciding "what to do next". So in practice, a few simple heuristics are used each time the scheduler needs to decide which thread to let run next:
   - there's usually **a fast path** for determining that the currently running thread is still the most appropriate one to continue running (e.g. storing a bitmask of which priorities have runnable threads, so the scheduler can quickly determine that there's none of a higher priority than that currently running);
   - if there is a runnable **thread of higher priority** than the currently running one, then the higher priority one will be scheduled in3;
   - if a thread is "preempted" in this way, it is generally allowed to keep its remaining quantum and continue running when the higher-priority thread is scheduled out again;
   - when a thread's **quantum runs out**, the thread is **"put to the back of the queue"** of runnable threads with the given priority and if there's no queued (runnable) thread of higher priority, then next thread of the same priority will be scheduled in;
   - at the end of its quantum, if there's "nothing better to run", then a **thread could immediately get a new quantum and continue running**;
   - a thread typically gets a temporary boost to its quantum and/or priority at strategic points.
- Quantum and priority boosting
Both Windows and Linux (kernel 2.6.8 onwards) implement temporary boosting. Strategic points at which a thread may be given a "boost" include:
   - when it has just finished waiting for a lock/signal or I/O5;
   - when it has not run for a long time (in Windows, this appears to be a simple priority boost after a certain time; in Linux, there is an ongoing calculation based on the thread's nice value and its recent resource usage);
   - when a GUI event occurs;
   - while it owns the focussed window (recent versions of Windows give threads of the owning process a larger quantum; earlier versions give them a priority boost).

#### Context switching
- context switching. Roughly speaking, this is the procedure that takes place when the system switches between threads running on the available CPUs.
- the thread scheduler must actually manage the various thread structures and make decisions about which thread to schedule next where, and every time the thread running on a CPU actually changes— often referred to as a context switch
- switching between **threads of different processes** (that is, switching to a thread that belongs to a different process from the one last running on that CPU) **will carry a higher cost**, since the address-to-memory mappings must be changed, and the contents of the cache almost certainly will be irrelevant to the next process.
- Context switches appear to typically have a cost somewhere between 1 and 10 microseconds (i.e. between a thousandth and a hundredth of a millisecond) between the fastest and slowest cases (same-process threads with little memory contention vs different processes). So the following are acceptable:
1 nanoseconds is billionth of one second, 
1 microsecond is millionth of one second,
1 millisecond is thousandth of one second

##### What causes too many slow context switches in Java?
- Every time we **deliberately** change a thread's status or attributes (e.g. by sleeping, waiting on an object, changing the thread's priority etc), we will cause a context switch. But usually we don't do those things so many times in a second to matter. Typically, the cause of excessive context switching comes from contention on shared resources, **particularly synchronized locks**:
   - rarely, a single object very frequently synchronized on could become a bottleneck;
   - more frequently, a complex application has several different objects that are each synchronized on with moderate frequency, but overall, threads find it difficult to make progress because they **keep hitting different contended locks** at regular intervals.

##### Avoiding contention and context switches in Java

- Firstly, before hacking with your code, a first course of action is upgrading your JVM, particularly if you are not yet using Java 6. Most new Java JVM releases have come with improved synchronization optimisation.
- Then, a high-level solution to avoiding synchronized lock contention is generally to use the various classes from the Java 5 concurrency framework (see the java.util.concurrent package). For example, instead of using a HashMap with appropriate synchronization, a ConcurrentHashMap can easily double the throughput with 4 threads and treble it with 8 threads (see the aforementioned link for some ConcurrentHashMap performance measurements). A replacement to synchronized with often better concurrency is offered with various explicit lock classes (such as ReentrantLock).

###### Java thread priority
- Lower-priority threads are given CPU when all higher priority threads are waiting (or otherwise unable to run) at that given moment.
- Thread priority **isn't very meaningful when all threads are competing for CPU**.
- The number should lie in the range of two constants **MIN_PRIORITY and MAX_PRIORITY defined on Thread**, and will typically reference **NORM_PRIORITY**, the default priority of a thread if we don't set it to anything else.
- For example, to give a thread a priority that is "half way between normal and maximum", we could call:
```java
thr.setPriority((Thread.MAX_PRIORITY - Thread.NORM_PRIORITY) / 2);
```

####### Some points about thread property
- depending on your OS and VM version, Thread.setPriority() may actually **do nothing at all** (see below for details);
- what thread priorities **mean to the thread scheduler differs from scheduler to scheduler**, and may not be what you intuitively presume; in particular: **Priority may not indicate "share of the CPU"**. As we'll see below, it turns out that "priority" is more or less an indication of CPU distribution on UNIX systems, but not under Windows.
- thread priorities are usually a **combination of "global" and "local" priority settings**, and Java's setPriority() method typically works only on the local priority— in other words, you can't set priorities across the entire range possible (this is actually a form of protection— you generally don't want, say, the mouse pointer thread or a thread handling audio data to be preempted by some random user thread);
- the number of distinct priorities available differs from system to system, but Java defines 10 (numbered 1-10 inclusive), so you could end up with threads that have different priorities under one OS, but the same priority (and hence unexpected behaviour) on another;
- most operating systems' thread schedulers actually perform **temporary manipulations** to thread priorities at strategic points (e.g. when a thread receives an event or I/O it was waiting for), and often "the OS knows best"; trying to manually manipulate priorities could just interfere with this system;
- your application **doesn't generally know what threads are running in other processes**, so the effect on the overall system of changing the priority of a thread may be hard to predict. So you might find, for example, that your low-priority thread designed to "run sporadically in the background" hardly runs at all due to a virus dection program running at a slightly higher (but still 'lower-than-normal') priority, and that the performance unpredictably varies depending on which antivirus program your customer is using. Of course, effects like these will always happen to some extent or other on modern systems.

## Thread scheduling implications in Java

### Thread Control
- the granularity and responsiveness of the Thread.sleep() method is largely determined by **the scheduler's interrupt** period and by how quickly the slept thread becomes the "chosen" thread again;
- the precise function of the setPriority() method depends on the specific OS's interpretation of priority (and which underlying API call Java actually uses when several are available): for more information, see the more detailed section on thread priority;
- the behaviour of the Thread.yield() method is similarly determined by what particuar underlying API calls do, and which is actually chosen by the VM implementation.

### "Granularity" of threads
- Although our introduction to threading focussed on how to create a thread, it turns out that **it isn't appropriate to create a brand new thread just for a very small task**. Threads are actually quite a "coarse-grained" unit of execution, for reasons that are hopefully becoming clear from the previous sections.

### Overhead and limits of creating and destroying threads
- creating and tearing down threads isn't free: there'll be some CPU overhead each time we do so;
- there may be some moderate limit on the number of threads that can be created, determined by the resources that a thread needs to have allocated (if a process has 2GB of address space, and each thread as 512K of stack, that means a maximum of a few thousands threads per process).

### Avoiding thread overhead in Java
- In applications such as servers that need to continually execute short, multithreaded tasks, the usual way to avoid the overhead of repeated thread creation is to create a thread pool. 

# Dinnig Philosophers problem
- The problem was designed to **illustrate the challenges of avoiding deadlock**, a system state in which no progress is possible. To see that a proper solution to this problem is not obvious, consider a proposal in which each philosopher is instructed to behave as follows:
1. think until the left fork is available; when it is, pick it up;
1. think until the right fork is available; when it is, pick it up;
1. when both forks are held, eat for a fixed amount of time;
1. then, put the right fork down;
1. then, put the left fork down;
1. repeat from the beginning.
- This attempted solution fails because it allows the system to reach a deadlock state, in which no progress is possible. This is a state in which each philosopher has picked up the fork to the left, and is waiting for the fork to the right to become available, vice versa. With the given instructions, this state can be reached, and when it is reached, the philosophers will eternally wait for each other to release a fork
- **Resource starvation** might also occur independently of deadlock if a particular philosopher is unable to acquire both forks because of a timing problem. For example, there might be a rule that the philosophers put down a fork after waiting ten minutes for the other fork to become available and wait a further ten minutes before making their next attempt.
- This scheme eliminates the possibility of deadlock (the system can always advance to a different state) but still **suffers from the problem of livelock**. If all five philosophers appear in the dining room **at exactly the same time** and each picks up the left fork at the same time the philosophers will wait ten minutes until they all put their forks down and then wait a further ten minutes before they all pick them up again.
## Solutions
### Arbitrator solution
Another approach is to guarantee that a philosopher can only pick up both forks or none by introducing an arbitrator, e.g., a waiter. In order to pick up the forks, a philosopher must ask permission of the waiter. The waiter gives permission to only one philosopher at a time until the philosopher has picked up both of their forks. Putting down a fork is always allowed. The waiter can be implemented as a mutex. In addition to introducing a new central entity (the waiter), this approach can result in reduced parallelism. if a philosopher is eating and one of their neighbors is requesting the forks, all other philosophers must wait until this request has been fulfilled even if forks for them are still available.

# Queue
## What is the difference between poll() and remove() method of Queue interface? (answer)
- Though both poll() and remove() method from Queue is used to remove the object and returns the head of the queue, there is a subtle difference between them. If Queue is empty() then a call to **remove() method will throw Exception**, while a call to **poll() method returns null**.

## What is the difference between fail-fast and fail-safe Iterators?
- Fail-fast Iterators **throws ConcurrentModificationException** when one Thread is iterating over collection object and **other** thread **structurally modify** Collection either by adding, removing or modifying objects on underlying collection. They are called fail-fast because they try to immediately throw Exception when they encounter failure. On the other hand **fail-safe Iterators** works on **copy of collection instead of original collection**

## To remove entry from collection
- you need to use Iterator's remove() method. This method removes current element from Iterator's perspective. If you use Collection's or List's remove() method during iteration then your code will throw **ConcurrentModificationException**. That's why it's advised **to use Iterator remove() method to remove objects from Collection**.

## What is the difference between Synchronized Collection and Concurrent Collection?
- One Significant difference is that **Concurrent Collections has better performance than synchronized Collection ** because they **lock only a portion of Map** to achieve concurrency and Synchronization.

## When do you use ConcurrentHashMap in Java
- ConcurrentHashMap is better suited for situation where you have **multiple readers** and **one
Writer or fewer writers** since Map gets locked only during the write operation. **If you have an equal number of reader and writer** than ConcurrentHashMap will perform in the line of **Hashtable or synchronized HashMap**.

## Sorting collections
-  Sorting is implemented using Comparable and Comparator in Java and when you call Collections.sort() it gets sorted based on the **natural order specified in compareTo()** method while Collections.sort(Comparator) will sort objects based on **compare() method of Comparator**. 

## Hashmap vs Hasset
- HashSet implements java.util.Set interface and that's why **only contains unique elements**, while **HashMap allows duplicate values**.  In fact, HashSet is actually implemented on top of java.util.HashMap.

## What is NavigableMap in Java
- NavigableMap Map was added in Java 1.6, it adds navigation capability to Map data structure. It provides methods like lowerKey() to get keys which is less than specified key, floorKey() to return keys which is less than or equal to specified key, ceilingKey() to get keys which is greater than or equal to specified key and higherKey() to return keys which is greater specified key from a Map. It also provide similar methods to get entries e.g. lowerEntry(), floorEntry(), ceilingEntry() and higherEntry(). Apart from navigation methods, it also provides utilities to create sub-Map e.g. creating a Map from entries of an exsiting Map like tailMap, headMap and subMap. headMap() method returns a NavigableMap whose keys are less than specified, tailMap() returns a NavigableMap whose keys are greater than the specified and subMap() gives a NavigableMap between a range, specified by toKey to fromKey

## Array vs ArrayList
- Array is fixed length data structure, once created you can not change it's length. On the other hand, **ArrayList is dynamic**, it automatically allocate a new array and copies content of old array, when it resize.
- Another reason of using ArrayList over Array is **support of Generics**.

## Can we replace Hashtable with ConcurrentHashMap?
- Since **Hashtable locks whole Map instead of a portion of Map**, **compound operations like if(Hashtable.get(key) == null) put(key, value) works in Hashtable** but **not in concurrentHashMap**. instead of this **use putIfAbsent() method of ConcurrentHashMap**

## What is CopyOnWriteArrayList, how it is different than ArrayList and Vector
- CopyOnWriteArrayList is new List implementation introduced in Java 1.5 which provides better concurrent access than Synchronized List. better concurrency is achieved by Copying ArrayList over each write and replace with original instead of locking. Also CopyOnWriteArrayList doesn't throw any ConcurrentModification Exception. Its different than ArrayList because its thread-safe and ArrayList is not thread-safe and it's different than Vector in terms of Concurrency. CopyOnWriteArrayList provides better Concurrency by reducing contention among readers and writers.

## Why ListIterator has added() method but Iterator doesn't or Why to add() method is declared in ListIterator and not on Iterator. (answer)
- ListIterator has added() method because of its ability to traverse or iterate in both direction of the collection. it maintains two pointers in terms of previous and next call and in a position to add a new element without affecting current iteration.

## What is BlockingQueue, how it is different than other collection classes? (answer)
- BlockingQueue is a Queue implementation available in java.util.concurrent package. It's one of the concurrent Collection class added on Java 1.5, main difference between BlockingQueue and other collection classes is that apart from storage, **it also provides flow control**. It can be used in inter-thread communication and also provides **built-in thread-safety by using happens-before guarantee**. You can use BlockingQueue to solve Producer Consumer problem, which is what is needed in most of concurrent applications.

## You have thread T1, T2 and T3, how will you ensure that thread T2 run after T1 and thread T3 run after T2
- To use **join** method.


# Happen before
- In computer science, the happened-before relation (denoted: → {\displaystyle \to \;} \to \;) is a relation between the result of two events, such that if one event should happen before another event, the result must reflect that, even if those events are in reality executed out of order (usually to optimize program flow). 
- In Java specifically, a happens-before relationship is a guarantee that **memory written to by statement A is visible to statement B**, that is, that statement **A completes its write before** statement B **starts its read**

# Concurrent framework
- The advantage of using Callable over Runnable is that **Callable** can explicitly **return a value**.
- Executors are a big step forward compared to plain old threads because **executors ease the management of concurrent tasks**. 
- Some types of algorithms exist that require tasks to create subtasks and communicate with each other to complete. Those are the **“divide and conquer” algorithms**, which are also referred to as **“map and reduce,”** in reference to the eponymous functions in functional languages.
- The fork/join framework added to the java.util.concurrent package in Java SE 7 through Doug Lea’s efforts fills that gap. The Java SE 5 and Java SE 6 versions of java.util.concurrent helped in **dealing with concurrency**, and the additions in Java SE 7 help with **parallelism**.
-  First and foremost, fork/join tasks should operate as **“pure” in-memory algorithms in which no I/O operations** come into play. Also, communication between tasks through shared state should be avoided as much as possible, because that implies that locking might have to be performed.
- The core addition is a new **ForkJoinPool executor** that is dedicated to running instances implementing ForkJoinTask. ForkJoinTask objects **support the creation of subtasks plus waiting for the subtasks to complete**. With those clear semantics, the **executor is able to dispatch tasks** among its **internal threads pool** by **“stealing” jobs when a task is waiting** for another task to complete and **there are pending tasks to be run**.
- ForkJoinTask objects feature two specific methods:
   - The fork() method allows a ForkJoinTask to be planned for asynchronous execution. This allows a new ForkJoinTask to be launched from an existing one.
   - In turn, the join() method allows a ForkJoinTask to wait for the completion of another one.
- There are two types of ForkJoinTask specializations:
   - Instances of **RecursiveAction** represent executions that **do not yield a return value**.
   - In contrast, instances of **RecursiveTask yield return values**.
In general, RecursiveTask is preferred because most divide-and-conquer algorithms return a value from a computation over a data set. 
- The fork and join principle consists of two steps which are performed recursively. These two steps are the fork step and the join step. 
- A task that uses the fork and join principle can fork (split) itself into smaller subtasks which can be executed concurrently. This is illustrated in the diagram below: 
- By splitting itself up into subtasks, each **subtask can be executed in parallel by different CPUs**, or **different threads on the same CPU**. 
- **The limit for when** it makes sense to fork a task into subtasks **is also called a threshold**. It is up to each task to decide on a sensible threshold. It depends very much on the kind of work being done.
- Once the subtasks have finished executing, the task may **join (merge) all the results into one result**.
- Of course, not all types of tasks may return a result. If the tasks do not return a result then a task just waits for its subtasks to complete. No result merging takes place then. 
- The **ForkJoinPool is a special thread pool** which is designed to work well with fork-and-join task splitting. The ForkJoinPool located in the java.util.concurrent package, so the full class name is java.util.concurrent.ForkJoinPool. 
- You create a ForkJoinPool using its constructor. As a parameter to the ForkJoinPool constructor you **pass the indicated level of parallelism** you desire. 
- The parallelism level **indicates how many threads or CPUs** you want to work concurrently on on tasks passed to the ForkJoinPool.
- You submit tasks to a ForkJoinPool **similarly to how you submit tasks to an ExecutorService**. You can submit two types of tasks. A task that **does not return any result (an "action"**), and a **task which does return** a result (a "task").

## Fork/Join framework details
- ForkJoinPool is consists of ForkJoinTask array and ForkJoinWorkerThread array.  
   - ForkJoinTask array contains tasks submitted to ForkJoinPool
   - ForkJoinWorkerThread array in charge of executing those tasks
   - When you call fork method on ForkJoinTask, program will call "pushTask" asynchronously of ForkJoinWorkerThread, and then return result right away.
   - "pushTask" will put current task into ForkJoinTask array queue, then execute "signalWork()" of ForkJoinPool to create a new thread to execute task.
   ```java
   final void pushTask(ForkJoinTask t) {
        ForkJoinTask[] q; int s, m;
        if ((q = queue) != null) {    // ignore if queue removed
            long u = (((s = queueTop) & (m = q.length - 1)) << ASHIFT) + ABASE;
            UNSAFE.putOrderedObject(q, u, t);
            queueTop = s + 1;         // or use putOrderedInt
            if ((s -= queueBase) <= 2)
                pool.signalWork();
	else if (s == m)
                growQueue();
        }
    }
   ```
   - "join" method main functionality is blocking current thread and wait for resutls.
   ```java
		public final V join() {
        if (doJoin() != NORMAL)
            return reportResult();
        else
            return getRawResult();
		}
		private V reportResult() {
				int s; Throwable ex;
				if ((s = status) == CANCELLED)
					throw new CancellationException();
		if (s == EXCEPTIONAL && (ex = getThrowableException()) != null)
					UNSAFE.throwException(ex);
				return getRawResult();
		}
   ```
	- When do call doJoin(), you can get status of curent thread. There are 4 status:
	   - NORMAL: completed
	   - CANCELLED
	   - SIGNAL
	   - EXCEPTIONAL
	- The method of doJoin()
	```java
	private int doJoin() {
        Thread t; ForkJoinWorkerThread w; int s; boolean completed;
        if ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) {
            if ((s = status) < 0)
				return s;
            if ((w = (ForkJoinWorkerThread)t).unpushTask(this)) {
                try {
                    completed = exec();
                } catch (Throwable rex) {
                    return setExceptionalCompletion(rex);
                }
                if (completed)
                    return setCompletion(NORMAL);
            }
            return w.joinTask(this);
        }
        else
            return externalAwaitDone();
    }
	```

## newTaskFor

If a SocketUsingTask is cancelled through its Future, the socket is closed and the

As of **Java 6, ExecutorService implementations can override newTaskFor** in AbstractExecutorService **to control instantiation of the Future corresponding to a submitted Callable or Runnable**. The default implementation just creates a new FutureTask, as shown in Listing 6.12. 
```java
protected <T> RunnableFuture<T> newTaskFor(Callable<T> task) { 
return new FutureTask<T>(task); 
} 
```
Listing 6.12. Default implementation of newTaskFor in ThreadPoolExecutor.

## Thread shutdown
- Sensible encapsulation practices dictate that you should not manipulate a thread—interrupt it, modify its priority, etc.—unless you own it. The thread API has no formal concept of thread ownership: a thread is represented with a Thread object that can be freely shared like any other object. However, it makes sense **to think of a thread as having an owner**, and this **is usually the class that created the thread**. So **a thread pool owns its worker threads**, and if those threads need to be interrupted, the thread pool should take care of it.
- As with any other encapsulated object, **thread ownership is not transitive**: the application may own the service and the service may own the worker threads, but **the application doesn’t own the worker threads and therefore should not attempt to stop them directly**. Instead, the service should provide lifecycle methods for shutting itself down that also shut down the owned threads; then the application can shut down the service, and the service can shut down the threads. Executor- Service provides the shutdown and shutdownNow methods; other thread-owning services should provide a similar shutdown mechanism.

## Log service implemented by blocking queue
- If you are logging multiple lines as part of a single log message, you may need to use additional client-side locking to prevent undesirable interleaving of output from multiple threads. If two threads logged multiline stack traces to the same stream with one println call per line, the results would be interleaved unpredictably, and could easily look like one large but meaningless stack trace.

```java
public class LogWriter {
private final BlockingQueue<String> queue; private final LoggerThread logger;
public LogWriter(Writer writer) {
this.queue = new LinkedBlockingQueue<String>(CAPACITY); this.logger = new LoggerThread(writer);
}
public void start() { logger.start(); }
public void log(String msg) throws InterruptedException { queue.put(msg);
}
private class LoggerThread extends Thread { private final PrintWriter writer;
...
public void run() {
  try {
    while (true)
writer.println(queue.take());
} catch(InterruptedException ignored) { } finally {
    writer.close();
}
} }
}
```

### Stop logging

- However, this approach has race conditions that make it unreliable. The implementation of log is a check-then-act sequence: producers could observe that the service has not yet been shut down but still queue messages after the shutdown, again with the risk that the producer might get blocked in log and never become unblocked. There are tricks that reduce the likelihood of this (like having the consumer wait several seconds before declaring the queue drained), but these do not change the fundamental problem, merely the likelihood that it will cause a failure.

```java
public void log(String msg) throws InterruptedException { 
    if (!shutdownRequested)
        queue.put(msg);
    else
  throw new IllegalStateException("logger is shut down");
}
```
- The way to provide reliable shutdown for LogWriter is to fix the race con- dition, which means making the submission of a new log message atomic. But we don’t want to hold a lock while trying to enqueue the message, since put could block. Instead, we can atomically check for shutdown and conditionally increment a counter to “reserve” the right to submit a message, as shown in Log- Service in Listing 7.15.


### Delegate shutdown to high level service
```java

public class LogService {
private final ExecutorService exec = newSingleThreadExecutor(); ...
public void start() { }
public void stop() throws InterruptedException { try {
exec.shutdown();
exec.awaitTermination(TIMEOUT, UNIT);
        } finally {
            writer.close();
} }
public void log(String msg) { try {
 } }
exec.execute(new WriteTask(msg));
} catch (RejectedExecutionException ignored) { }

```

- It can even delegate to one shot Executor, OneShotExecutionService.java
```java
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Created by todzhang on 2017/1/30.
 * If a method needs to process a batch of tasks and does not return
 * until all the tasks are finished, it can simplify service lifecycle management
 * by using a private Executor whose lifetime is bounded by that method.
 *
 *
 * The checkMail method in Listing checks for new mail in parallel
 * on a number of hosts. It creates a private executor and submits
 * a task for each host: it then shuts down the executor and waits
 * for termination, which occurs when all
 */
public class OneShotExecutionService {


    boolean checkMail(Set<String> hosts, long timeout, TimeUnit unit) throws InterruptedException{
        ExecutorService exec= Executors.newCachedThreadPool();
        final AtomicBoolean hasNewMail=new AtomicBoolean(false);
        try {
            for (final String host : hosts
                    ) {
                exec.execute(new Runnable() {
                    @Override
                    public void run() {
                        if (checkMail(host)) {
                            hasNewMail.set(true);
                        }
                    }
                });
            }
        }
        finally{
            exec.shutdown();
            exec.awaitTermination(timeout,unit);
        }
        return hasNewMail.get();
    }

    boolean checkMail(String host){
        return true;
    }
}

```

- When an ExecutorService is shut down abruptly with shutdownNow, it attempts to cancel the tasks currently in progress and returns a list of tasks that were sub- mitted but never started so that they can be logged or saved for later processing. Detailed logic can be found at [CancelledTaskTrackingExecutor.java](https://github.com/CloudsDocker/algo/blob/master/algoWS/src/main/java/com/todzhang/CancelledTaskTrackingExecutor.java)
- The leading cause of premature thread death is RuntimeException.

# JVM shutdown
- The JVM can shut down in either an _orderly_ or _abrupt_ manner. An orderly shut- down is initiated when the last “normal” (nondaemon) thread terminates, some- one calls System.exit, or by other platform-specific means (such as sending a SIGINT or hitting Ctrl-C). While this is the standard and preferred way for the JVM to shut down, it can also be shut down abruptly by calling **Runtime.halt or by killing the JVM process** through the operating system (such as sending a SIGKILL).

## Shutdown hooks
- In an orderly shutdown, the JVM first starts all registered shutdown hooks. Shutdown hooks are unstarted threads that are registered with **Runtime.addShutdownHook**. The JVM makes no guarantees on the order in which shutdown hooks are started. If any application threads (daemon or nondaemon) are still running at shutdown time, they continue to run concurrently with the shutdown process. 
- When all shutdown hooks have completed, the JVM may choose **to run finalizers if runFinalizersOnExit is true**, 
- and then halts. 
- The JVM makes no attempt to stop or interrupt any application threads that are still running at shutdown time; they are abruptly terminated when the JVM eventually halts. If the shutdown hooks or finalizers don’t complete, then the orderly shutdown process “hangs” and the JVM must be shut down abruptly. In an abrupt shutdown, the JVM is not required to do anything other than halt the JVM; shutdown hooks will not run.
- Shutdown **hooks should be thread-safe**: they must **use synchronization when accessing shared data** and should be careful to avoid deadlock, just like any other concurrent code. Further, they should not make assumptions about the state of the application (such as whether other services have shut down already or all normal threads have completed) or about why the JVM is shutting down, and **must therefore be coded extremely defensively**. 
- Finally, they **should exit as quickly as possible**, since their existence delays JVM termination at a time when the user may be expecting the JVM to terminate quickly.
- Shutdown hooks can be used for service or **application cleanu**p, such as deleting temporary files or cleaning up resources that are not automatically cleaned up by the OS. Listing 7.26 shows how LogService in Listing 7.16 could register a shutdown hook from its start method to ensure the log file is closed on exit.
- Because shutdown hooks all run concurrently, closing the log file could cause trouble for other shutdown hooks who want to use the logger. To avoid this problem, shutdown hooks should not rely on services that can be shut down by the application or other shutdown hooks. **One way to accomplish this is to use a single shutdown hook for all services**, rather than one for each service, and have it call a series of shutdown actions. This ensures that shutdown actions execute sequentially in a single thread, thus avoiding the possibility of race conditions or deadlock between shutdown actions. This technique can be used whether or not you use shutdown hooks; **executing shutdown actions sequentially rather than concurrently** eliminates many potential sources of failure. 
```java
public void start() { 
  Runtime.getRuntime().addShutdownHook(new Thread() {
        public void run() {
          try { LogService.this.stop(); }
          catch (InterruptedException ignored) {}
} });
}
```

### Daemon thread
- Threads are divided into two types: **normal threads and daemon threads**. When the **JVM starts up**, all the threads it creates (such as garbage collector and other housekeeping threads) **are daemon threads**, except the main thread. When a new thread is created, it inherits the daemon status of the thread that created it, so by default any threads created by the main thread are also normal threads. 
- Normal threads and daemon threads **differ only in what happens when they exit**. When a thread exits, the JVM performs an inventory of running threads, and **if the only threads that are left are daemon threads, it initiates an orderly shutdown**. When the JVM halts, **any remaining daemon threads are abandoned— finally blocks are not executed**, stacks are not unwound—the JVM just exits.
- **Daemon threads should be used sparingly**—few processing activities can be safely abandoned at any time with no cleanup. In particular, it is **dangerous to use daemon threads for tasks that might perform any sort of I/O**. Daemon threads are best saved for “housekeeping” tasks, such as a background thread that periodically removes expired entries from an in-memory cache.
Daemon threads are not a good substitute for properly managing the life- cycle of services within an application.

### Finalizer
- Finalizers offer **no guarantees** on **when or even if they run**, and they impose a significant performance cost on objects with nontrivial finalizers. They are also extremely difficult to write correctly.9 In most cases, the combination of finally blocks and explicit close methods does a better job of resource management than finalizers; the sole exception is when you need to manage objects that hold resources acquired by native methods.
- **Java does not provide a preemptive mechanism** for cancelling activities or terminating threads. Instead, **it provides a cooperative interruption mechanism** that can be used to facilitate cancellation, but it is up to you to construct protocols for cancellation and use them consistently. Using **FutureTask and the Executor framework simplifies building cancellable tasks and services**.

# Thread Pool
- Thread pools work best when tasks are homogeneous and independent. Mix- ing long-running and short-running tasks risks “clogging” the pool unless it is very large; submitting tasks that depend on other tasks risks deadlock unless the pool is unbounded. Fortunately, requests in typical network-based server applications—web servers, mail servers, file servers—usually meet these guide- lines.
- Some tasks have characteristics that require or preclude a specific exe- cution policy. Tasks that depend on other tasks require that the thread pool be large enough that tasks are never queued or rejected; tasks that exploit thread confinement require sequential execution. Document these requirements so that future maintainers do not undermine safety or live- ness by substituting an incompatible execution policy.
- In a single-threaded executor, a task that submits another task to the same executor and waits for its result **will always deadlock**.
- The same thing can happen in larger thread pools if all threads are executing tasks that are blocked waiting for other tasks still on the work queue. This is called **thread starvation deadlock**, and can occur whenever a pool task initiates an unbounded blocking wait for some resource or condition that can succeed only through the action of another pool task, such as waiting for the return value or side effect of another task, unless you can guarantee that the pool is large enough.

> Whenever you submit to an Executor tasks that are not independent, be aware of the possibility of thread starvation deadlock, and document any pool sizing or configuration constraints in the code or configuration file where the Executor is configured.

- Task that deadlocks in a single-threaded Executor. Don’t do this.
```java
Future<String> header,footer;
            header=exec.submit(new LoadFileTask("header.html"));
            footer=exec.submit(new LoadFileTask("footer.html"));
            String body=renderBody();
            return header.get()+body+footer.get();
```

# Long running tasks
- Thread pools can have responsiveness problems if tasks can block for extended periods of time, even if deadlock is not a possibility. A thread pool can become clogged with long-running tasks, increasing the service time even for short tasks. If the pool size is too small relative to the expected steady-state number of long- running tasks, eventually all the pool threads will be running long-running tasks and responsiveness will suffer.
- **One technique that can mitigate the ill effects** of long-running tasks is for tasks **to use timed resource waits instead of unbounded waits**. Most blocking methods in the plaform libraries come in both untimed and timed versions, such as Thread.join, BlockingQueue.put, CountDownLatch.await, and Selector.sel- ect. If the wait times out, you can mark the task as failed and abort it or requeue it for execution later. This guarantees that each task eventually makes progress towards either successful or failed completion, freeing up threads for tasks that might complete more quickly. If a thread pool is frequently full of blocked tasks, this may also be a sign that the pool is too small.

# size the thread pool
- The ideal size for a thread pool depends on the types of tasks that will be submitted and the characteristics of the deployment system. **Thread pool sizes should rarely be hard-coded**; instead pool sizes should be provided by a **configuration** mechanism or computed dynamically by consulting **Runtime.availableProcessors**.
- If you have different categories of tasks with very different behaviors, consider using multiple thread pools so each can be tuned according to its workload.
- The optimal pool size for keeping the processors at the desired utilization is:
Nthreads=Ncpu∗Ucpu∗ (1+((W/C)
Ncpu: Number of CPU
Ucpu: target CPU utilization , 0<Ucpu<1
W/C: ratio of wait time to compute time

# ThreadPoolExecutor
- ThreadPoolExecutor provides the base implementation for the executors re- turned by the newCachedThreadPool, newFixedThreadPool, and newScheduled- ThreadExecutor factories in Executors. 
- Implementation of ThreadPoolExecutor
```java
public ThreadPoolExecutor(int corePoolSize,int maximumPoolSize, long keepAliveTime, TimeUnit unit, BlockingQueue<Runnable> workQueue,ThreadFactory threadFactory,RejectedExecutionHandler handler){...}
```
1. corePoolSize is the target size, the implementation attempts to maintain the pool at this size when there are no tasks to execute. and will not create more threads than this unless the work queue is full. When a ThreadPoolExecutor is initially created, the core threads are **not started immediately**, but instead as tasks are submitted. Unless you call **prestartAllCoreThreads**
1. The maximum pool size is the upper bound on how many threads can be active at once.
1. A thread that has been idel for longer than the **keep-alive time** becomes a candidate for reaping and can be terminated if the current **pool size exceed the core size**.
- By tuning the core pool size and keep-alive times, you can encourage the pool to reclaim resources used by otherwise idle threads, making them available for more useful work. (Like everything else, this is a tradeoff: reaping idle threads incurs additional latency due to thread creation if threads must later be created when demand increases.)
- The **newFixedThreadPool** factory sets **both the core pool size and the maxi- mum pool size** to the **requested pool size**, creating the effect of **infinite timeout**; 
- the **newCachedThreadPool** factory sets the **maximum pool size to Integer.MAX_VALUE** and the **core pool size to zero** with a **timeout of one minute**, creating the effect of an **infinitely expandable thread pool** that will contract again when demand decreases. 
- Other combinations are possible using the explicit ThreadPool- Executor constructor.
- ThreadPoolExecutor allows you to supply a BlockingQueue to hold tasks awaiting execution. There are **three basic approaches to task queueing**: **un- bounded queue, bounded queue, and synchronous handoff**. The choice of queue interacts with other configuration parameters such as pool size.
- The default for **newFixedThreadPool and newSingleThreadExecutor** is to use an **unbounded LinkedBlockingQueue**. Tasks will queue up if all worker threads are busy, but the queue could grow without bound if the tasks keep arriving faster than they can be executed.
- A more stable resource management strategy is to use a bounded queue, such as an ArrayBlockingQueue or a bounded LinkedBlockingQueue or Priority- BlockingQueue. Bounded queues help prevent resource exhaustion but introduce the question of what to do with new tasks when the queue is full. (There are a number of possible **saturation policies** for addressing this problem;
- For very large or unbounded pools, you can also bypass queueing entirely and instead hand off tasks directly from producers to worker threads using a SynchronousQueue. **A SynchronousQueue is not really a queue at all, but a mechanism for managing handoffs between threads**. In order to put an element on a SynchronousQueue, another thread must already be waiting to accept the handoff. If no thread is waiting but the current pool size is less than the maximum, ThreadPoolExecutor creates a new thread; otherwise the task is rejected according to the saturation policy. **Using a direct handoff is more efficient because the task can be handed right to the thread that will execute it, rather than first placing it on a queue and then having the worker thread fetch it from the queue**. Synchron- ousQueue is a practical choice only if the pool is unbounded or if rejecting excess tasks is acceptable. The newCachedThreadPool factory uses a SynchronousQueue.
- Using a FIFO queue like LinkedBlockingQueue or ArrayBlockingQueue causes tasks to be started in the order in which they arrived. For more con- trol over task execution order, you can use a PriorityBlockingQueue, which orders tasks according to priority. Priority can be defined by natural order (if
tasks implement Comparable) or by a Comparator.
- The newCachedThreadPool factory is a good default choice for an Executor, providing better queuing performance than a fixed thread pool.5 A fixed size thread pool is a good choice when you need to limit the number of concurrent tasks for resource-management purposes, as in a server application that accepts requests from network clients and would otherwise be vulnerable to overload.
- ith tasks that depend on other tasks, bounded thread pools or queues can cause thread starvation deadlock; instead, use an unbounded pool configuration like newCachedThreadPool.

# Saturation policies
- When a bounded work queue fills up, the **saturation policy** comes into play. The saturation policy for a ThreadPoolExecutor can be modified by calling setRejectedExecutionHandler. 
- Several implementations of RejectedExecutionHandler are provided, each implementing a different saturation policy: **AbortPolicy, CallerRunsPolicy, DiscardPolicy, and DiscardOldestPolicy**.
- The default policy, **abort**, causes execute to throw the unchecked Rejected- ExecutionException; the caller can catch this exception and implement its own overflow handling as it sees fit. The **discard** policy silently discards the newly submitted task if it cannot be queued for execution; the **discard-oldest** policy discards the task that would otherwise be executed next and tries to resubmit the new task. (If the work queue is a priority queue, this discards the highest-priority element, so the combination of a discard-oldest saturation policy and a priority queue is not a good one.)
- The **caller-runs policy** implements a form of throttling that neither discards tasks nor throws an exception, but instead tries to slow down the flow of new tasks by pushing some of the work back to the caller. It executes the newly submitted task not in a pool thread, but in the thread that calls execute. If we modified our WebServer example to use a bounded queue and the caller-runs policy, after all the pool threads were occupied and the work queue filled up the next task would be executed in the main thread during the call to execute. 

# Thread Factory
- Whenever a thread pool needs to create a thread, it does so through a thread factory (see Listing 8.5). The default thread factory creates a new, nondaemon thread with no special configuration. Specifying a thread factory allows you to customize the configuration of pool threads. **ThreadFactory has a single method, newThread, that is called whenever a thread pool needs to create a new thread**.
- There are a number of reasons to use a custom thread factory. You might want to specify an UncaughtExceptionHandler for pool threads, or instantiate an instance of a custom Thread class, such as one that performs debug logging.
```java
public interface ThreadFactory{
    Thread newThread(Runnable r);
}
```
- BoundedExecutor.java is using semaphore and Executor for bounded executor service.
- MyThreadFactory.java and MyAppThread.java are used to customize ThreadFactory, a customized Thread.
- MyExtendedThreadPool.java implemented beforeExecute, afterExecute, etc method to add statistics, such as log and timing for each operations in the thread pool

## Process sequential processing to parallel
```java
void processSequentially(List<Element> elements) { for (Element e : elements)
process(e);
}
void processInParallel(Executor exec, List<Element> elements) { for (final Element e : elements)
exec.execute(new Runnable() {
public void run() { process(e); }
}); }
```
- If you want to submit a set of tasks and wait for them all to complete, you can use **ExecutorService.invokeAll**; to retrieve the results as they become available, you can use a **CompletionService**.

# Deadlocks
- There is often a tension between safety and liveness. We use locking to ensure thread safety, but indiscriminate use of locking can cause **lock-ordering deadlocks**. Similarly, we **use thread pools and semaphores to bound resource consumption**, but failure to understand the activities being bounded can cause **resource deadlocks**. Java applications do not recover from deadlock, so it is worthwhile to ensure that your design precludes the conditions that could cause it. 
- When a thread holds a lock forever, other threads attempting to acquire that lock will block forever waiting. When thread A holds lock L and tries to acquire lock M, but at the same time thread B holds M and tries to acquire L, both threads will wait forever. This situation is the simplest case of deadlock (or deadly embrace),
- Database systems are designed to detect and recover from deadlock. A trans- action may acquire many locks, and locks are held until the transaction commits. So it is quite possible, and in fact not uncommon, for two transactions to deadlock. Without intervention, they would wait forever (holding locks that are probably re- quired by other transactions as well). But the database server is not going to let this happen. When it detects that a set of transactions is deadlocked (which it does by searching the is-waiting-for graph for cycles), it picks a victim and aborts that transaction. This releases the locks held by the victim, allowing the other transactions to proceed. The application can then retry the aborted transaction, which may be able to complete now that any competing transactions have com- pleted.
- A program will be free of lock-ordering deadlocks if all threads acquire the locks they need in a fixed global order.

## To break deadlock by ensuring lock order
-  uses System.identityHashCode to induce a lock ordering. It involves a few extra lines of code, but eliminates the possibility of deadlock.
```java
 public static native int identityHashCode(Object x);
```
- In the rare case that two objects have the same hash code, we must use an arbitrary means of ordering the lock acquisitions, and this reintroduces the pos- sibility of deadlock. To prevent inconsistent lock ordering in this case, a third “tie breaking” lock is used. By acquiring the tie-breaking lock before acquiring either Account lock, we ensure that only one thread at a time performs the risky task of acquiring two locks in an arbitrary order, eliminating the possibility of deadlock (so long as this mechanism is used consistently). If hash collisions were common, this technique might become a concurrency bottleneck (just as having a single, program-wide lock would), but because hash collisions with System.identity- HashCode are vanishingly infrequent, this technique provides that last bit of safety at little cost.
- two locks are acquired by two threads in different orders, risking deadlock.
- Calling a method **with no locks held is called an open call** [CPJ 2.4.1.3], and classes that rely on open calls are more well-behaved and composable than classes that make calls with locks held. Using open calls to avoid deadlock is analogous to using encapsulation to provide thread safety: while one can certainly construct a thread-safe program without any encapsulation, the thread safety analysis of a program that makes effective use of encapsulation is far easier than that of one that does not.

## Avoiding and diagnosing deadlocks
- A program that **never acquires more than one lock at a time cannot experience lock-ordering deadlock**. Of course, this is not always practical, but if you can get away with it, it’s a lot less work. If you must **acquire multiple locks, lock ordering must be a part of your design**: try to **minimize the number of potential locking interactions**, and follow and document a lock-ordering protocol for locks that may be acquired together.
- In programs that use fine-grained locking, audit your code for deadlock free- dom using a two-part strategy: first, identify where multiple locks could be ac- quired (try to make this a small set), and then perform a global analysis of all such instances to ensure that lock ordering is consistent across your entire pro- gram. Using open calls wherever possible simplifies this analysis substantially. With no non-open calls, finding instances where multiple locks are acquired is fairly easy, either by code review or by automated bytecode or source code anal- ysis.

## Timed lock attempts
- Another technique for detecting and recovering from deadlocks is to use the timed tryLock feature of the explicit Lock classes (see Chapter 13) instead of intrinsic locking. Where intrinsic locks wait forever if they cannot acquire the lock, explicit locks let you specify a timeout after which tryLock returns failure.

## JVM Thread dump including dead lock
- There are two threads trying to accquire two locks in different orders
- 
```bash
Java stack information for the threads listed above: "ApplicationServerThread ":
at MumbleDBConnection.remove_statement
- waiting to lock <0x650f7f30> (a MumbleDBConnection) at MumbleDBStatement.close
- locked <0x6024ffb0> (a MumbleDBCallableStatement)
...
"ApplicationServerThread ":
at MumbleDBCallableStatement.sendBatch
- waiting to lock <0x6024ffb0> (a MumbleDBCallableStatement) at MumbleDBConnection.commit
- locked <0x650f7f30> (a MumbleDBConnection)
```

# Other liveness hazards
- While deadlock is the most widely encountered liveness hazard, there are sev- eral other liveness hazards you may encounter in concurrent programs including starvation, missed signals, and livelock.


# Reference 
- http://www.javamex.com/tutorials/threads/thread_scheduling.shtml
- http://www.javamex.com/tutorials/threads/priority.shtml
- http://www.javamex.com/tutorials/threads/how_threads_work.shtml
- http://www.javamex.com/tutorials/threads/thread_scheduling_2.shtml
- http://www.javamex.com/tutorials/threads/yield.shtml
- http://javarevisited.blogspot.in/2012/07/countdownlatch-example-in-java.html
- http://javarevisited.blogspot.sg/2012/05/how-to-use-threadlocal-in-java-benefits.html
- http://javarevisited.blogspot.com/2012/03/simpledateformat-in-java-is-not-thread.html
- http://javarevisited.blogspot.com/2012/05/counting-semaphore-example-in-java-5.html#ixzz4WRuTQFDF
- http://javarevisited.blogspot.in/2012/02/what-is-race-condition-in.html          
- http://javarevisited.blogspot.in/2011/05/wait-notify-and-notifyall-in-java.html
- http://javarevisited.blogspot.in/2015/07/how-to-use-wait-notify-and-notifyall-in.html
- http://javarevisited.blogspot.in/2012/07/cyclicbarrier-example-java-5-concurrency-tutorial.html
- http://javarevisited.blogspot.in/2011/09/fork-join-task-java7-tutorial.html
- https://en.wikipedia.org/wiki/Dining_philosophers_problem
- http://javarevisited.blogspot.com/2011/11/collection-interview-questions-answers.html#ixzz4WTN72QPa
- http://javarevisited.blogspot.in/2011/11/collection-interview-questions-answers.html
- http://www.oracle.com/technetwork/articles/java/fork-join-422606.html
- http://tutorials.jenkov.com/java-util-concurrent/java-fork-and-join-forkjoinpool.html
- http://coopsoft.com/ar/CalamityArticle.html
- http://www.infoq.com/cn/articles/fork-join-introduction
