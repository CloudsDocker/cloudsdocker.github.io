---
layout: page
title: Java-Tricky-Tech-Questions.md
tags:
- java
- Questions
---
# What's seed in Java
Since the next number in a pseudorandom generator is determined by the pre- vious number(s), such a generator always needs **a place to start, which is called its seed**. The sequence of numbers generated for **a given seed will always be the same**. The seed for an instance of the java.util.Random class can be set in its constructor or with its setSeed() method.

# Cipher
- Given a variable c that is known to be an uppercase letter, the Java computation, j = c − 'A' produces the desired index j. **As a sanity check**, if character c is 'A', then j = 0. When c is 'B', the difference is 1.

# Uncaught exception handler
- The Thread API also provides **the UncaughtExceptionHandler facility, which lets you detect when a thread dies due to an uncaught exception**. The two approaches are complementary: taken together, they provide defense-in- depth against thread leakage.
- When **a thread exits due to an uncaught exception**, the **JVM reports this event to an application-provided UncaughtExceptionHandler** (see Listing 7.24); if no handler exists, the default behavior is to print the stack trace to System.err
- In long-running applications, always use uncaught exception handlers for all threads that at least log the exception.
- To set an UncaughtExceptionHandler for pool threads, provide a ThreadFac- tory to the ThreadPoolExecutor constructor.
- Somewhat confusingly, exceptions thrown from tasks make it to the uncaught exception handler **only for tasks submitted with execute** ; for tasks submitted with submit, any thrown exception, checked or not, is considered to be part of the task’s return status. If a task submitted with submit terminates with an exception, it is rethrown by Future.get, wrapped in an ExecutionException.
```java
public class UEHLogger implements Thread.UncaughtExceptionHandler{
  public void uncaughtException(Thread t, Throwable e){
    Logger logger=Logger.getAnonymousLogger();
    logger.log(Level.SEVERE, "Thread terminated with exception:"+e.getName(),e);
  }
}
```

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

# Java Generics ? , E and T what is the difference?
Well there's no difference between the first two - they're just using different names for the type parameter (E or T).

The third isn't a valid declaration - ? is used as a wildcard which is used when providing a type argument, e.g. List<?> foo = ... means that foo refers to a list of some type, but we don't know what.

# Question: What does the following Java program print?

public class Test {
    public static void main(String[] args) {
        System.out.println(Math.min(Double.MIN_VALUE, 0.0d));
    }
}

## Anwser 0.0d
The Double.MIN_VALUE is 2^(-1074), a double constant whose magnitude is the least among all double values. 


# What will happen if you put return statement or System.exit () on try or catch block? Will finally block execute?
Answer of this tricky question in Java is that **finally block will execute even if you put a return statement** in the try block or catch block but finally block **won't run if you call System.exit()** from try or catch block. 

# Question: Can you override a private or static method in Java?

Another popular Java tricky question, As I said method overriding is a good topic to ask trick questions in Java. Anyway, you **can not override a private or static method** in Java, if you **create a similar method with same return type and same method arguments in child class** then it will **hide the superclass method**, this is known as **method hiding**.

Similarly, you cannot override a private method in sub class because it's not accessible there, what you do is create another private method with the same name in the child class. See Can you override a private method in Java or more details

# Question: What do the expression 1.0 / 0.0 will return? will it throw Exception? any compile time error?

Answer: This is another tricky question from Double class. Though Java developer knows about the double primitive type and Double class, while doing floating point arithmetic they don't pay enough attention to Double.INFINITY , NaN, and -0.0
and other rules that govern the arithmetic calculations involving them. The simple answer to this question is that it will not throw ArithmeticExcpetion and **return Double.INFINITY**.

Also, note that the comparison **x == Double.NaN always evaluates to false**, even if x itself is a NaN. To test if x is a NaN, one should use the method call Double.isNaN(x) to check if given number is NaN or not. If you know SQL, this is very close to NULL there. 


# Overloading vs Overriding
- Main difference comes from the fact that method **overloading is resolved during compile time**, while method **overriding is resolved at runtime**
- Also rules of overriding or overloading a method are different in Java. 
   - a private, static and final method cannot be overriding in Java but you can still overload them
   - overriding both name and signature of the method must remain same, but in for overloading method, the signature must be different
   - call to **overloaded** methods are **resolved using static binding** while the call to **overridden method is resolved using dynamic binding** in Java.
- Java programmer to declare method with same name but different behavior. Method overloading and method overriding is based on Polymorphism in Java.
- In case of method overloading, method with same name co-exists in **same class** but they must have **different method signature**, while in case of method **overriding**, method with **same name** is declared in **derived class or sub class**
- If you have **two methods with same name** in one Java class **with different method signature** than its called **overloaded** method in Java. You can also overload constructor in Java
- Since **return type is not part of method signature** simply changing return type will result in duplicate method and you will get compile time error in Java.
- you can also **overload private and final method** in Java but you **can not override** them
- When you **override a method** in Java its signature remains exactly same **including return type**. Rules of override:
   - Method signature must be same including return type, number of method parameters, type of parameters **and order of parameters** . Be advised: as of Java 5, you're allowed to change the return type in the overriding method as long as the new return type is a subtype of the declared return type of the overridden (super class) method
   - Overriding method **can not throw higher Exception** than original or overridden method. means if original method throws IOException than overriding method can not throw super class of IOException e.g. Exception but it can throw any sub class of IOException or simply does not throw any Exception. This rule only applies to checked Exception in Java, overridden method is free to throw any unchecked Exception. 
   - Overriding method **can not reduce accessibility of overridden method** , means if original or overridden method is public than overriding method **can not make it protected**. 
- Another important point is that you **can not override static method** in Java because **they are associated with Class** **rather than object** and resolved and **bonded during compile time** and that’s the reason you cannot override main method in Java
- From Java 5 onwards you can use annotation in Java to declare overridden method just like we did with @override. ** @override annotation allows compiler** , IDE like NetBeans and Eclipse **to cross verify or check**  if this method is really overrides super class method or not.


# Static vs. Dynamic binding
- **private, final and static methods and variables uses static binding** and bonded by compiler while **virtual methods** are bonded during **runtime** based upon runtime object.
- Here is sample of static binding 
```java
public class StaticBindingTest {
      public static void main(String args[])  {
       Collection c = new HashSet();
       StaticBindingTest et = new StaticBindingTest();
       et.sort(c);
          }
   
    //overloaded method takes Collection argument
    public Collection sort(Collection c){
        System.out.println("Inside Collection sort method");
        return c;
    }

   //another overloaded method which takes HashSet argument which is sub class
    public Collection sort(HashSet hs){
        System.out.println("Inside HashSet sort method");
        return hs;
    }
      }
Output: Inside Collection sort method
```
**because it was bonded on compile time based on type of variable (Static binding)  which was collection.**

- Here is sample of dynamic binding 
```java
public class DynamicBindingTest {
    public static void main(String args[]) {
        Vehicle vehicle = new Car(); //here Type is vehicle but object will be Car
        vehicle.start();       //Car's start called because start() is overridden method
    }
}

class Vehicle {
    public void start() {
        System.out.println("Inside start method of Vehicle");
    }
}

class Car extends Vehicle {
    @Override
    public void start() {
        System.out.println("Inside start method of Car");
    }
}

Output: Inside start method of Car
```

In summary, bottom line is static binding is a compile time operation while dynamic binding is a runtime. one uses Type and other uses Object to bind. static, private and final methods and variables are resolved using static binding which makes there execution fast because no time is wasted to find correct method during runtime.

# Static in Java
- static keyword can not be applied on top level class. Making a top level class static in Java will result in compile time error.
-  Beware that if your static initialize block throws Exception than you may **get java.lang.NoClassDefFoundError** when you try to access the class which failed to load.
-  **Static method can not be overridden** in Java as they belong to class and not to object
```java
 public class TradingSystem {

    public static void main(String[] args) {
        TradingSystem system = new DirectMarketAccess();
        DirectMarketAccess dma = new DirectMarketAccess();
        
        // static method of Instrument class will be called,

        // even though object is of sub-class DirectMarketAccess
        system.printCategory();
        
        //static method of EquityInstrument class will be called
        dma.printCategory();
    }

    public static void printCategory(){
        System.out.println("inside super class static method");
    }
}

class DirectMarketAccess extends TradingSystem{
    public static void printCategory(){
        System.out.println("inside sub class static method");
    }
}

Output:
inside super class static method
inside sub class static method
```
- This shows that static method can not be overridden in Java and concept of method overloading doesn't apply to static methods. Instead declaring same static method on Child class **is known as method hiding** in Java
- Consider **making a static variable final** in Java to make it constant and avoid changing it from anywhere in the code
- when to use Singleton vs Static Class in Java for those purpose,answer is that if its **completely stateless** and it work on provided data then you can **go for static class** **otherwise Singleton** pattern is a better choice.
## When to make a method static in Java
- Method **doesn't depends on object's state**, in other words **doesn't depend on any member variable** and **everything they need is passes as parameter** to them
- Utility methods are good candidate of making static in Java because then they can directly be accessed using class name without even creating any instance. Classic example is java.lang.Math
- Static method in Java is very popular to implement Factory design pattern. Since Generics also provides type inference during method invocation, use of static factory method to create object is popular Java idiom. 

# Phone interview
-  Key to success in telephonic interview is **to the point** and **concise answer**.

## Difference between String, StringBuffer and StringBuilder in Java
- String is **immutable** while both StringBuffer and StringBuilder **is mutable**, which means any change e.g. converting String to upper case or trimming white space will **produce another instance** rather than changing the same instance. On later two, **StringBuffer is synchronized** while **StringBuilder is not**, in fact its a ditto replacement of StringBuffer added in Java 1.5.
## Difference between extends Thread vs implements Runnable in Java? 
- Difference comes from the fact that you **can only extend one class** in Java, which means if you extend Thread class you lose your opportunity to extend another class, on the other hand if you implement Runnable, you can still extend another class.

## Difference between Runnable and Callable interface in Java? 
- Runnable was the only way to implement a task in Java which can be executed in parallel before JDK 1.5 adds Callable. Just like Runnable, Callable also defines a single **call() method** but unlike run() it **can return values and throw exceptions**.

## Difference between ArrayList and LinkedList in Java? 
- In short, ArrayList is backed by array in Java, while **LinkedList is just collection of nodes**, similar to linked list data structure. ArrayList also provides **random search** if you know the index, while **LinkedList only allows sequential search**. On other hand, **adding and removing element from middle** is **efficient in LinkedList** as compared to ArrayList because it only require to modify links and no other element is rearranged.

## What is difference between wait and notify in Java? 
- Both wait and notify methods are used for **inter thread communication**, where **wait is used to pause** the thread on a condition and **notify is used to send notification** to waiting threads. Both must be called from synchronized context e.g. **synchronized method or block**.


## Difference between HashMap and Hashtable in Java? 
- Though both HashMap and Hashtable are based upon hash table data structure, there are subtle difference between them. HashMap is non synchronized while Hashtable is synchronized and because of that HashMap is faster than Hashtable, as there is no cost of synchronization associated with it. One more minor difference is that HashMap allows a null key but Hashtable doesn't.


# Check a number is prime or not
- We learned numbers are prime if the only divisors they have are 1 and itself. Trivially, we can check every integer from 1 to itself (exclusive) and test whether it divides evenly. Check the source code of ** PrimeTester.java**
   - naive approach:  We learned numbers are prime if the only divisors they have are 1 and itself. Trivially,  we can check every integer from 1 to itself (exclusive)  and test whether it divides evenly.
   ```java
   for(int i=2;2*i<=n;i++){
			if(n%i==0)
   ```
   - power of 2 approach:    further enhance, as if 2 divides some interger n, then (n/2) divides n as well so we'll times of 2. Please be advised in for loop, should use 2*i<=n, rather than "<n",   otherwise, 4 will be return as ture mistakely
   ```java
   for(int i=2;2*i<=n;i++){
			if(n%i==0)
   ```
   - isPrimeSquare approach:  	 we notice that you really only have to go up to the square root of n,   because if you list out all of the factors of a number,  the square root will always be in the middle Finally, we know 2 is the "oddest" prime - it happens to be the only even prime number. Because of this, we need only check 2 separately, then traverse  odd numbers up to the square root of n.  In the end, our code will resemble this:
   ```java
   // check if n is a multiple of 2
   if(n>2&&n%2==0)
			return false;		
		// if not, then just check the odds
		for(int i=3;i*i<=n;i+=2){
			if(n%i==0) 
   ```
# Difference between abstract class and interface? 
- From Java 8 onwards difference between abstract class and interface in Java has minimized, now even interface can have implementation in terms of default and static method. BTW, in Java you can still extend just one class but can extend multiple inheritance. Abstract class is used to provide default implementation with just something left to customize, while interface is used heavily in API to define contract of a class.

# How to Swap Two Numbers without Temp or Third variable in Java - Interview Question
## Swapping two numbers without using temp variable in Java
```java
int a = 10;
int b = 20;
System.out.println("value of a and b before swapping, a: " + a +" b: " + b);

//swapping value of two numbers without using temp variable
a = a+ b; //now a is 30 and b is 20
b = a -b; //now a is 30 but b is 10 (original value of a)
a = a -b; //now a is 20 and b is 10, numbers are swapped

System.out.println("value of a and b after swapping, a: " + a +" b: " + b);
Output:
value of a and b before swapping, a: 10 b: 20
value of a and b after swapping, a: 20 b: 10
```
## Swapping two numbers without using temp variable in Java with bitwise operator
```java
int a = 2; //0010 in binary
int b = 4; //0100 in binary
System.out.println("value of a and b before swapping, a: " + a +" b: " + b);
// 6  is     0110
//swapping value of two numbers without using temp variable and XOR bitwise operator     
a = a^b; //now a is 6 (0110) and b is 4(0100)
b = a^b; //now a is 6 but b is 2 (0010) (original value of a)
a = a^b; //now a is 4 and b is 2, numbers are swapped

System.out.println("value of a and b after swapping using XOR bitwise operation, a: " + a +" b: " + b);
value of a and b before swapping, a: 2 b: 4
value of a and b after swapping using XOR bitwise operation, a: 4 b: 2
```

## Swapping two numbers without using temp variable in Java with division and multiplication
- There is another, third way of swapping two numbers without using third variable, which involves multiplication and division operator. 
```java
int a = 6;
int b = 3;
System.out.println("value of a and b before swapping, a: " + a +" b: " + b);

//swapping value of two numbers without using temp variable using multiplication and division
a = a*b; //now a is 18 and b is 3
b = a/b; //now a is 18 but b is 6 (original value of a)
a = a/b; //now a is 3 and b is 6, numbers are swapped

System.out.println("value of a and b after swapping using multiplication and division, a: " + a +" b: " + b);
Output:
value of a and b before swapping, a: 6 b: 3
value of a and b after swapping using multiplication and division, a: 3 b: 6
```
- That's all on 3 ways to swap two variables without using third variable in Java. Its good to know multiple ways of swapping two variables without using temp or third variable to handle any follow-up question. Swapping numbers **using bitwise operator is the fastest** among three, because it **involves bitwise operation**. It’s also great way to show your knowledge of bitwise operator in Java and impress interviewer, which then may ask some question on bitwise operation. A nice trick to drive interview on your expert area.

# Bitwise operator
- "~" inverts a bit pattern; it can be applied to any of the integral types, making every "0" a "1" and every "1" a "0".
- The bitwise & operator performs a bitwise AND operation.
- The bitwise ^ operator performs a bitwise exclusive OR operation.
- The bitwise | operator performs a bitwise inclusive OR operation.


# How to check if linked list contains loop in Java?
- Algorithm to find if linked list contains loops or cycles. Two pointers, fast and slow is used while iterating over linked list. **Fast pointer moves two nodes** in each iteration, while **slow pointer moves to one node**. If linked list contains loop or cycle than both **fast and slow pointer will meet** at some point during iteration. If they don't meet and fast or slow will point to null, then linked list is not cyclic and it doesn't contain any loop. 
1. Use two pointers fast and slow
1. Move fast two nodes and slow one node in each iteration
1. If fast and slow meet then linked list contains cycle
1. if fast points to null or fast.next points to null then linked list is not cyclic
- This algorithm is also known as Floyd’s cycle finding algorithm and popularly **known as tortoise and hare algorithm** to find cycles in linked list. Sample can be found via "LoopInList.java"



# Reference 
- http://www.java67.com/2012/09/top-10-tricky-java-interview-questions-answers.html
- http://javarevisited.blogspot.in/2012/03/what-is-static-and-dynamic-binding-in.html
- http://www.java67.com/2015/03/top-40-core-java-interview-questions-answers-telephonic-round.html
- http://www.mkyong.com/java/how-to-determine-a-prime-number-in-java/
- http://javarevisited.blogspot.in/2013/02/swap-two-numbers-without-third-temp-variable-java-program-example-tutorial.html
- http://docs.oracle.com/javase/tutorial/java/nutsandbolts/op3.html
- http://javarevisited.blogspot.in/2013/05/find-if-linked-list-contains-loops-cycle-cyclic-circular-check.html
