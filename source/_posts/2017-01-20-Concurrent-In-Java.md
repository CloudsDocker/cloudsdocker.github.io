---
layout: page
title: Java Concurrent
tags:
- java
- concurrent
---
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

# Wait & Notify
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

# Fork-Join
- Fork/join tasks is “pure” in-memory algorithms in which no I/O operations come into picture.it is based on a work-stealing algorithm. 
- Java’s most attractive part is it makes things easier and easier.
- its really challenging where several threads are working together to accomplish a large task so again java has tried to make things easy and simplifies this concurrency using Executors and Thread Queue.
- it work on **divide and conquer algorithm** and **create sub-tasks and communicate with each other to complete**.
- New fork-join executor framework has been created which is responsible for creating one new task object which is again responsible for creating new sub-task object and waiting for sub-task to be completed.internally it maintains a thread pool and executor assign pending task to this thread pool to complete when one task is waiting for another task to complete. whole Idea of fork-join framework is to leverage multiple processors of advanced machine.

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

## What is the difference between Iterator and Enumeration
- Iterator duplicate functionality of Enumeration with one addition of **remove() method**
- Another difference is that Iterator is more safe than Enumeration and doesn't allow another thread to modify collection object during iteration except remove() method and **throws ConcurrentModificaitonException**.

## How does HashSet is implemented in Java, How does it use Hashing
- HashSet is built on top of HashMap. If you look at source code of java.util.HashSet class, you will find that that it uses a HashMap with same values for all keys, as shown below:
```java
private transient HashMap map;
// Dummy value to associate with an Object in the backing Map
private static final Object PRESENT = new Object();
// When you call add() method of HashSet, it put entry in HashMap :
public boolean add(E e) {
  return map.put(e, PRESENT)==null;
}
```
## What do you need to do to use a custom object as a key in Collection classes like Map or Set? (answer)
- If you are using any custom object in Map as key, you need to **override equals() and hashCode() method**, and make sure they **follow their contract**. 
- On the other hand if you are storing a custom object **in Sorted Collection** e.g. SortedSet or SortedMap, you also need to make sure that your **equals() method is consistent to compareTo() method**, otherwise that collection will not follow there contacts e.g. Set may allow duplicates.

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

As of Java 6, ExecutorService implementations can override newTaskFor in AbstractExecutorService to control instantiation of the Future corresponding to a submitted Callable or Runnable. The default implementation just creates a new FutureTask, as shown in Listing 6.12. 
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


# Reference 
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
