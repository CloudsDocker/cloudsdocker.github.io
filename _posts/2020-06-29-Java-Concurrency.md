---
title: Concurrency in Java
date: 2020-06-29
layout: posts
---

# How to make thread-safe

## You can create a new object for each method call

Sample code as SpelExpressionParser in Spring
```java

public class SpelExpressionParser extends TemplateAwareExpressionParser {
	//....
	// Be noticed it will new a object each time, so it's thread safe
	@Override
	protected SpelExpression doParseExpression(String expressionString, @Nullable ParserContext context) throws ParseException {
		return new InternalSpelExpressionParser(this.configuration).doParseExpression(expressionString, context);
	}

}
```


# :books:Concepts
Threads are sometimes called lightweight processes, and most modern operating systems treat threads, not processes, as the basic units of scheduling.


## Liveness

`While safety means "nothing bad ever happens", liveness concerns the complementary goal that "something good eventually happens"`.
A liveness failure occurs when an activity gets into a state such that it is permanently unable to make forward progress.


## thread-safety

Whether an object needs to be thread-safe depends on whether it will be accessed from multiple threads. This is a property of how the object is used in a program, not what it does. Making an object thread-safe requires using synchronization to coordinate access to its mutable state; failing to do so could result in data corruption and other undesirable consequences.

Whenever more than one thread accesses a given state variable, and one of them might write to it, they all must coordinate their access to it using synchronization. The primary mechanism for synchronization in Java is the synchronized keyword, which provides exclusive locking, but the term "synchronization" also includes the use of volatile variables, explicit locks, and atomic variables.

## How to fix borken multithreading

If multiple threads access the same mutable state variable without appropriate synchronization, your program is broken. There are three ways to fix it:
- Don't share the state variable across threads;
- Make the state variable immutable;
- Use synchronization whenever accessing the state variable.

This "code confidence" is about as close as many of us get to correctness, so let's just assume that single-threaded correctness is something that "we know it when we see it".


`A class is thread-safe when it continues to behave correctly when accessed from multiple threads.`


> A class is thread-safe if it behaves correctly when accessed from multiple threads, regardless of the scheduling or interleaving of the execution of those threads by the runtime environment, and with no additional synchronization or other coordination on the part of the calling code.

## race condition
A race condition occurs when getting the right answer relies on lucky timing.

The most common type of race condition is check-then-act, where a potentially stale observation is used to make a decision on what to do next.

### check-then-act
It is this invalidation of observations that characterizes most race conditions— `using a potentially stale observation to make a decision or perform a computation`. **This type of race condition is called check-then-act**: you observe something to be true (file X doesn't exist) and then take action based on that observation (create X); but in fact the observation could have become invalid between the time you observed it and the time you acted on it (someone else created X in the meantime), causing a problem (unexpected exception, overwritten data, file corruption).

A common idiom that uses check-then-act is lazy initialization.


To ensure thread safety, check-then-act operations (like lazy initialization) and read-modify-write operations (like increment) must always be atomic.


### Sample

```java
this. @NotThreadSafe
public class LazyInitRace {        
  private ExpensiveObject instance = null;        
  public ExpensiveObject getInstance() {               
    if (instance == null)                   
    instance = new ExpensiveObject();               
    return instance;        
  }
}

```

### consequences
Like most concurrency errors, race conditions don't always result in failure: some unlucky timing is also required. But race conditions can cause serious problems.


## Intrinsic lock

Every Java object can implicitly act as a lock for purposes of synchronization; these built-in locks are called intrinsic locks or monitor locks. The lock is automatically acquired by the executing thread before entering a synchronized block and automatically released when control exits the synchronized block, whether by the normal control path or by throwing an exception out of the block.

Intrinsic locks in Java act as mutexes (or mutual exclusion locks), which means that at most one thread may own the lock. When thread A attempts to acquire a lock held by thread B, A must wait, or block, until B releases it. If B never releases the lock, A waits forever.


# Reentrancy lock
Reentrancy means that locks are acquired on a per-thread rather than per-invocation basis.[7] Reentrancy is implemented by associating with each lock an acquisition count and an owning thread. When the count is zero, the lock is considered unheld.

When a thread acquires a previously unheld lock, the JVM records the owner and sets the acquisition count to one. If that same thread acquires the lock again, the count is incremented, and when the owning thread exits the synchronized block, the count is decremented. When the count reaches zero, the lock is released.


## Guarding State with Locks
Because locks enable serialized access to the code paths they guard, we can use them to construct protocols for guaranteeing exclusive access to shared state. Following

However, just wrapping the compound action with a synchronized block is not sufficient; if synchronization is used to coordinate access to a variable, it is needed everywhere that variable is accessed. Further, when using locks to coordinate access to a variable, the same lock must be used wherever that variable is accessed.

> It is a common mistake to assume that synchronization needs to be used only when writing to shared variables; this is simply not true.
For each mutable state variable that may be accessed by more than one thread, all accesses to that variable must be performed with the same lock held. In this case, we say that the variable is guarded by that lock.



The fact that every object has a built-in lock is just a convenience so that you needn't explicitly create lock objects.[9]

Every shared, mutable variable should be guarded by exactly one lock. Make it clear to maintainers which lock that is.
