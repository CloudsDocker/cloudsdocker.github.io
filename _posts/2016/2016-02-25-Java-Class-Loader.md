---
layout: posts
title: Java Class Loader
tags:
 - Java
 - class loader`
---

# Codecache
- The maximum size of the code cache is set via the -XX:ReservedCodeCacheSize=N flag (where N is the default just mentioned for the particular compiler). The code cache is managed like most memory in the JVM: there is an initial size (specified by -XX:InitialCodeCacheSize=N). Allocation of the code cache size starts at the initial size and increases as the cache fills up. The total of native and heap memory used by the JVM yields the total footprint of an application.

1.  The code cache is a resource with a defined maximum size that affects the total amount of compiled code the JVM can run.
Tiered compilation can easily use up the entire code cache in its default configuration (particularly in Java 7); monitor the code cache and increase its size if necessary when using tiered compilation.
Compilation Thresholds
The major factor involved here is how often the code is executed; once it is executed a certain number of times, its compilation threshold is reached, and the com‐ piler deems that it has enough information to compile the code.
Compilation is based on two counters in the JVM: the number of times the method has been called, and the number of times any loops in the method have branched back. Branching back can effectively be thought of as the number of times a loop has com‐ pleted execution, either because it reached the end of the loop itself or because it executed a branching statement like continue.
When the JVM executes a Java method, it checks the sum of those two counters and decides whether or not the method is eligible for compilation. If it is, the method is queued for compilation So every time the loop completes an execution, the branching counter is incremented and inspected. If the branching counter has exceeded its indi‐ vidual threshold, then the loop (and not the entire method) becomes eligible for compilation.
This kind of compilation is called on-stack replacement (OSR), because even if the loop is compiled, that isn’t sufficient: the JVM has to have the ability to start executing the compiled version of the loop while the loop is still running. When the code for the loop has finished compiling, the JVM replaces the code (on-stack), and the next iteration of the loop will execute the much-faster compiled version of the code. Standard compilation is triggered by the value of the -XX:CompileThreshold=N flag. The default value of N for the client compiler is 1,500; for the server compiler it is 10,000. Changing the value of the CompileThreshold flag will cause the the compiler to choose to compile the code sooner (or later) than it normally would have.
Periodically (specifically, when the JVM reaches a safepoint), the value of each counter is reduced. Practically speaking, this means that the counters are a relative measure of the recent hotness of the method or loop. One side effect of this is that somewhat-frequently executed code may never be compiled, even for programs that run forever (these methods are sometimes called lukewarm [as opposed to hot]). This is one case where reducing the compilation threshold can be beneficial, and it is another reason why tiered compilation is usually slightly faster than the server compiler alone.
Quick Summary
1.  Compilation occurs when the number of times a method or loop has been executed reaches a certain threshold.
Changing the threshold values can cause the code to be com‐ piled sooner than it otherwise would.
“Lukewarm” methods will never reach the compilation thresh‐ old (particularly for the   server compiler) since the counters de‐ cay over time.
that give visibility into the working of the compiler. The most important of these is -XX:+PrintCompilation (which by default is false).
If PrintCompilation is enabled, every time a method (or loop) is compiled, the JVM prints out a line with information about what has just been compiled.
Usually this number will simply increase monotonically
Inspecting Compilation with jstat
Seeing the compilation log requires that the program be started with the -XX:+PrintCompilation flag. If the program was started without that flag, you can get some limited visibility into the working of the compiler by using jstat.
jstat has two options to provide information about the compiler. The -compiler option supplies summary information about how many methods have been compiled (here 5003 is the process ID of the program to be inspected):
% jstat -compiler 5003
Compiled Failed Invalid Time FailedType FailedMethod
206 0   0   1.97    0
Note this also lists the number of methods that failed to compile and the name of the last method that failed to compile; if profiles or other information lead you to suspect that a method is slow because it hasn’t been compiled, this is an easy way to verify that hypothesis.
Because jstat takes an optional argument to repeat its operation, you can see over time which methods are being compiled. In this example, jstat repeats the information for process ID 5003 every second (1,000 ms):
% jstat -printcompilation 5003 1000 Compiled

It’s easy to read OSR lines like this example as 25% and wonder about the other 75%, but remember that the number is the compilation ID, and the % just signifies OSR compilation.
1.  The best way to gain visibility into how code is being compiled is by enabling PrintCompilation.
Output from enabling PrintCompilation can be used to make sure that compilation is proceeding as expected.
If a method is compiled using standard compilation, then the next method invocation will execute the compiled method; if a loop is compiled using OSR, then the next iteration of the loop will execute the compiled code.
These queues are not strictly first in, first out: methods whose invocation counters are higher have priority.
this priority ordering helps to ensure that the most important code will be compiled first. (This is another reason why the compilation ID in the PrintCompilation output can appear out of order.)
When the client compiler is in use, the JVM starts one compilation thread; the server compiler has two such threads. When tiered compilation is in effect, the JVM will by default start multiple client and server threads based on a somewhat complex equation involving double logs of the number of CPUs on the target platform. The number of compiler threads (for all three compiler options) can be adjusted by setting the -XX:CICompilerCount=N flag (with a default value given in the previous table).
Quick Summary
1.  Compilation occurs asynchronously for methods that are placed on the compilation queue.
The queue is not strictly ordered; hot methods are compiled before other methods in the queue. This is another reason why compilation IDs can appear out of order in the compilation log.
Inlining
One of the most important optimizations the compiler makes is to inline methods. Code that follows good object-oriented design often contains a number of attributes that are accessed via getters (and perhaps setters):
public class Point { private int x, y;
public void getX() { return x; } public void setX(int i) { x = i; }
}
The overhead for invoking a method call like this is quite high, especially relative to the amount of code in the method. In fact, in the early days of Java, performance tips often argued against this sort of encapsulation precisely because of the performance impact of all those method calls. Fortunately, JVMs now routinely perform code inlining for these kinds of methods. Hence, you can write this code:
Point p = getPoint(); p.setX(p.getX() * 2);
and the compiled code will essentially execute this:
Point p = getPoint(); p.x = p.x * 2;
Inlining is enabled by default. It can be disabled using the -XX:-Inline flag, though it is such an important performance boost that you would never actually do that (for example, disabling inlining reduces the performance of the stock batching test by over 50%).

The basic decision about whether to inline a method depends on how hot it is and its size. The JVM determines if a method is hot (i.e., called frequently) based on an internal calculation; it is not directly subject to any tunable parameters. If a method is eligible for inlining because it is called frequently, then it will be inlined only if its bytecode size is less than 325 bytes (or whatever is specified as the -XX:MaxFreqInlineSize=N flag). Otherwise, it is eligible for inlining only if it is small: less than 35 bytes (or whatever is specified as the -XX:MaxInlineSize=N flag).
Sometimes you will see recommendations that the value of the MaxInlineSize flag be increased so that more methods are inlined.
Inlining is the most beneficial optimization the compiler can make, particularly for object-oriented code where attributes are well encapsulated.
1.  Tuning the inlining flags is rarely needed, and recommendations to do so often fail to account for the relationship between normal inlining and frequent inlining. Make sure to account for both cases when investigating the effects of inlining.
Escape Analysis
The server compiler performs some very aggressive optimizations if escape analysis is enabled (-XX:+DoEscapeAnalysis, which is true by default).
Escape analysis is the most sophisticated of the optimizations the compiler can perform. This is the kind of optimization that fre¬quently causes microbenchmarks to go awry.
1.  Escape analysis can often introduce “bugs” into improperly synchronized code.

Escape analysis is a technical that evaluate the scope of a Java object. In particular, if a java object allocated by some execting thread can ever be seen by a different thread, the object ‘escapes’.
For example, consider this class to work with factorials:
```java
public class Factorial {
private BigInteger factorial;
private int n;
public Factorial(int n) {
this.n = n;
}
public synchronized BigInteger getFactorial() {
if (factorial == null)
factorial = ...;
return factorial;
}
}
To store the first 100 factorial values in an array, this code would be used:
ArrayList<BigInteger> list = new ArrayList<BigInteger>(); for (int i = 0; i < 100; i++) {
Factorial factorial = new Factorial(i);
list.add(factorial.getFactorial());
}
```

The factorial object is referenced only inside that loop; no other code can ever access
that object. Hence, the JVM is free to perform a number of optimizations on that object:
·   It needn’t get a synchronization lock when calling the getFactorial() method.
·   It needn’t store the field n in memory; it can keep that value in a register. Similarly it can store the factorial object reference in a register.
·   In fact, it needn’t allocate an actual factorial object at all; it can just keep track of the individual fields of the object.
Deoptimization

There are two cases of deoptimization: when code is “made not entrant,” and when code is “made zombie.”
This generates a deoptimization trap, and the previous optimizations are discarded. If a lot of additional calls are made with logging enabled, the JVM will quickly end up compiling that code and making new optimizations.
The second thing that can cause code to be made not entrant is due to the way tiered compilation works. In tiered compilation, code is compiled by the client compiler, and then later compiled by the server compiler (and actually it’s a little more complicated than that,


Deoptimizing Zombie Code

When the compilation log reports that it has made zombie code, it is saying that it has reclaimed some previous code that was made not entrant. But there were still objects of the StockPriceHistoryImpl class around.
Eventually all those objects were reclaimed by GC. When that happened, the compiler noticed that the methods of that class were now eligible to be marked as zombie code.

The heap (usually) accounts for the largest amount of memory used by the JVM, but the JVM also uses memory for its internal operations. This nonheap memory is native memory. Native memory can also be allocated in applications (via JNI calls to malloc() and similar methods, or when using New I/O, or NIO). The total of native and heap memory used by the JVM yields the total footprint of an application.
1.  Deoptimization allows the compiler to back out previous versions of compiled code.
Code is deoptimized when previous optimizations are no longer valid (e.g., because the type of the objects in question has changed).
1.  There is usually a small, momentary effect in performance when code is deoptimized, but the new code usually warms up quick‐ ly again.
2.  Under tiered compilation, code is deoptimized when it had previously been compiled by the client compiler and has now been optimized by the server compiler.
Tiered Compilation Levels
It turns out that there are five levels of execution, because the client compiler has three different levels. So the level of compilation runs from:
·   0: Interpreted code
·   1: Simple C1 compiled code
·   2: Limited C1 compiled code
·   3: Full C1 compiled code
·   4: C2 compiled code
A typical compilation log shows that most methods are first compiled at level 3: full C1 compilation. (All methods start at level 0, of course.) If they run often enough, they will get compiled at level 4 (and the level 3 code will be made not entrant). This is the most frequent path: the client compiler waits to compile something until it has information about how the code is used that it can leverage to perform optimizations.
If the server compiler queue is full, methods will be pulled from the server queue and compiled at level 2, which is the level at which the C1 compiler uses the invocation and back-edge counters (but doesn’t require profile feedback). That gets the method com‐ piled more quickly; the method will later be compiled at level 3 after the C1 compiler has gathered profile information, and finally compiled at level 4 when the server compiler queue is less busy.

And of course when code is deoptimized, it goes to level 0.
Summary:
Tiered compilation can operate at five distinct levels among the two compilers
Changing the path between levels is not recommended; this section just helps to explain the output of the compilation log.
This chapter has provided a lot of details about how just-in-time compilation works. From a tuning perspective, the simple choice here is to use the server compiler with tiered compilation for virtually everything; this will solve 90% of compiler-related performance issues. Just make sure that the code cache is sized large enough, and the compiler will provide pretty much all the performance that is possible.
If you have some experience with Java performance, you may be surprised that compilation has been discussed for an entire chapter without mentioning the final keyword. In some circles, the final keyword is thought to be an important factor in performance because it is believed to allow the JIT compiler to make better choices about inlining and other optimizations.
Still, it is a persistent rumor. For the record, then, you should use the final keyword whenever it makes sense: for an immutable object or primitive value you don’t want to change, for parameters to certain inner classes, and so on. But the presence or absence of the final keyword will not affect the performance of an application.
Don’t be afraid of small methods—and in particular getters and setters—because they are easily inlined. If you have a feeling that the method overhead can be ex‐ pensive, you’re correct in theory (we showed that removing inlining has a huge impact on performance). But it’s not the case in practice, since the compiler fixes that problem.
2.  Code that needs to be compiled sits in a compilation queue. The more code in the queue, the longer the program will take to achieve optimal performance.
3.  Although you can (and should) size the code cache, it is still a finite resource.
4.  The simpler the code, the more optimizations that can be performed on it. Profile feedback and escape analysis can yield much faster code, but complex loop struc‐ tures and large methods limit their effectiveness.



That concept is the essential difference between committed (or allocated) memory and reserved memory (sometimes called the virtual size of a process). The JVM must tell the operating system that it might need as much as 2 GB of memory for the heap, so that memory is reserved: the operating system promises that when the JVM attempts to allocate additional memory when it increases the size of the heap, that memory will be available.
Still, only 512 MB of that memory is actually allocated initially, and that 512 MB is all of the memory that actually is being used (for the heap). That (actually allocated) mem‐ ory is known as the committed memory. The amount of committed memory will fluc‐ tuate as the heap resizes; in particular, as the heap size increases, the committed memory correspondingly increases.
When we look at performance, only committed memory really matters: there is never a performance problem from reserving too much memory.
However, sometimes you want to make sure that the JVM does not reserve too much memory. This is particularly true for 32-bit JVMs. Since the maximum process size of a 32-bit application is 4 GB (or less, depending on the operating system), over-reserving memory can be an issue. A JVM that reserves 3.5 GB of memory for the heap is left with only 0.5 GB of native memory for its stacks, code cache, and so on. It doesn’t matter if the heap only expands to commit 1 GB of memory: because of the 3.5 GB reservation, the amount of memory for other operations is limited to 0.5 GB.
64-bit JVMs aren’t limited that way by the process size, but they are limited by the total amount of virtual memory on the machine. Say that you have a small server with 4 GB of physical memory and 10 GB of virtual memory and start a JVM with a maximum

One exception to this is thread stacks. Every time the JVM creates a thread, the OS allocates some native memory to hold that thread’s stack, committing more memory to the process (until the thread exits, at least). Thread stacks, though, are fully allocated when they are created.

Code cache
The code cache uses native memory to hold compiled code. As discussed in Chap‐ ter 4, this can be tuned (though performance will suffer if all the code cannot be compiled due to space limitations).
Developers can allocate native memory via JNI calls, but NIO byte buffers will also allocate native memory if they are created via the allocateDirect() method. Native byte buffers are quite important from a performance perspective, since they allow native code and Java code to share data without copying it. The most common example here is buffers that are used for filesystem and socket operations. Writing data to a native NIO buffer and then sending that data to the channel or socket) requires no copying of data between the JVM and the C library used to transmit the data. If a heap byte buffer is used instead, contents of the buffer must be copied by the JVM.

The allocateDirect() method call is quite expensive; direct byte buffers should be reused as much as possible. The ideal situation is when threads are independent and each can keep a direct byte buffer as a thread-local variable. That can sometimes use too much native memory if there are many threads that need buffers of variable sizes, since eventually each thread will end up with a buffer at the maximum possible size. For that kind of situation—or when thread-local buffers don’t fit the application design— an object pool of direct byte buffers may be more useful.

1.  From a tuning perspective, the footprint of the JVM can be limi¬ted in the amount of native memory it uses for direct byte buf¬fers, thread stack sizes, and the code cache (as well as the heap).



# Class loader
- A class loader in Java is simply an object whose type extends the ClassLoader class. When the virtual machine needs access to a particular class, it asks the appropriate class loader.

- Class loaders are organized into a tree hierarchy. At the root of this tree is the system class loader. This class loader is also called the primordial class loader or the null class loader. It is used only to load classes from the core Java API.

- The system class loader has one or more children. It has at least one child; the URL class loader that is used to load classes from the classpath. It may have other direct children, though typically any other class loaders are children of the URL class loader that reads the classpath.

- The hierarchy comes into play when it is time to load a class. Classes are loaded in one of three ways: either explicitly by calling the loadClass( ) method of a class loader, explicitly by calling the Class.forName( ) method, or implicitly when they are referenced by an already−loaded class.
In any case, a class loader is asked to load the class. In the first case, the class loader is the object on which the loadClass( ) method is invoked. In the case of the forName( ) method, the class loader is either passed to that method, or it is the class loader that loaded the class that is calling the forName( ) method. The implicit case is similar: the class loader that was used to load the referencing class is also used to load the referenced class.
Class loaders are responsible for asking their parent to load a class; only if that operation fails will the class loader attempt to define the class itself.
 

- The net effect of this is that system classes will always be loaded from the system class loader, classes on the class path will always be loaded by the class loader that knows about the classpath, and in general, a class will be loaded by the oldest class loader in the ancestor hierarchy that knows where to find a class.

- When you create a class loader, you can insert it anywhere into the hierarchy of class loaders (except at the root). Typically, when a class loader is created, its parent is the class loader of the class that is instantiating the new class loader.


- Implementing a Class Loader

- Now we'll look at how to implement a class loader. The class loader we implement will be able to extend the normal permissions that are granted via policy files, and it will enforce certain optional security features of the class loader.

- The basic class that defines a class loader is the ClassLoader class (java.lang.ClassLoader):
public abstract class ClassLoader
Turn a series of Java bytecodes into a class definition. This class does not define how the bytecodes are obtained but provides all other functionality needed to create the class definition.

- However, the preferred class to use as the basis of a class loader is the SecureClassLoader class (java.security.SecureClassLoader):
public class SecureClassLoader extends ClassLoader
Turn a series of Java bytecodes into a class definition. This class adds secure functionality to the ClassLoader class, but it still does not define how bytecodes are obtained. Although this class is not abstract, you must subclass it in order to use it.
The secure class loader provides additional functionality in dealing with code sources and protection domains. You should always use this class as the basis of any class loader you work with; in fact, the ClassLoader class would be private were it not for historical reasons.

public class URLClassLoader extends SecureClassLoader
Load classes securely by obtaining the bytecodes from a set of given URLs.


# Key Methods of the Class Loader

- The ClassLoader class and its subclasses have three key methods that you work with when creating your own class loader.
6.3.2.1 The loadClass( ) method
The loadClass( ) method is the only public entry into the class loader:
public Class loadClass(String name)

- Load the named class. A ClassNotFoundException is thrown if the class cannot be found.
This is the simplest way to use a class loader directly: it requires that the class loader be instantiated and then be used via the loadClass( ) method. Once the Class object has been constructed, there are three ways in which a method in the class can be executed:
The correct implementation of the loadClass( ) method is crucial to the security of the virtual machine. For instance, one operation this method performs is to call the parent class loader to see if it has already defined a particular class; this allows all the
core Java classes to be loaded by the primordial class loader. If that operation is not performed correctly, security could suffer. As a developer you should be careful when you override this method; as an administrator, this is one of the reasons to prevent untrusted code from creating a class loader.

## 6.3.2.2 The findClass( ) method

- The loadClass( ) method performs a lot of setup and bookkeeping related to defining a class, but from a developer perspective, the bulk of the work in creating a Class class object is performed by the findClass( ) method:
protected Class findClass(String name)

- The findClass( ) method uses whatever mechanism it deems appropriate to load the class (e.g., by reading a class file from the file system or from an HTTP server). It is then responsible for creating the protection domain associated with the class and using the next method to create the Class class object.

- The defineClass( ) methods
These methods all take an array of Java bytecodes and some information that specifies the permissions associated with the class represented by those bytecodes. They all return the Class class object:
protected final Class defineClass(String name, byte[] b, int off, int len)


## Responsibilities of the Class Loader
When you implement a class loader, you override some or all of the methods we've just listed. In sum, the class loader must perform the following steps:
The security manager is consulted to see if this program is allowed to access the class in question. If it is not, a security exception is thrown. This step is optional; it should be implemented at the beginning of the loadClass( ) method. This

1.  corresponds to the use of the accessClassInPackage permission.
If the class loader has already loaded this class, it finds the previously defined class object and returns that object. This step is built into the loadClass( ) method.

2.  corresponds to the use of the accessClassInPackage permission.
If the class loader has already loaded this class, it finds the previously defined class object and returns that object. This step is built into the loadClass( ) method.

3.  Otherwise, the class loader consults its parent to see if the parent knows how to load the class. This is a recursive operation, so the system class loader

4.  will always be asked first to load a class. This prevents programs from providing alternate definitions of classes in the core API (but a clever class loader can defeat that protection). This step is built into the loadClass( ) method.
The security manager is consulted to see if this program is allowed to create the class in question. If it is not, a security exception is thrown. This step is optional; if implemented, it should appear at the beginning of the findClass( ) method. Note that this step should take place after the parent class loader is queried rather than at the beginning of the operation (as is done with the access check). No Sun−supplied class loader implements this step; it corresponds to the defineClassInPackage permission.
5.  The class file is read into an array of bytes. The mechanism by which the class loader reads the file and creates the byte array will vary depending on the class loader (which, after all, is one of the points of having different class loaders). This occurs in the findClass( ) method.
The appropriate protection domain is created for the class. This can come from the default security model (i.e., from the policy files), and it
6.  can be augmented (or even replaced) by the class loader. Alternately, you can create a code source object and defer definition of the protection domain. This occurs in the findClass( ) method.
7.  Within the findClass( ) method, a Class object is constructed from the bytecodes by calling the defineClass( ) method. If you used a code source in step 6, the getPermissions( ) method will be called to find the permissions associated with the code source. The defineClass( ) method also ensures that the bytecodes are run through the bytecode verifier.
8.  Before the class can be used, it must be resolved −− which is to say that any classes that it immediately references must also be found by this class loader. The set of classes that are immediately referenced contains any classes that the class extends as well as any classes used by the static initializers of the class. Note that classes that are used only as instance variables, method parameters, or local variables are not normally loaded in this phase: they are loaded when the class actually references them (although certain compiler optimizations may require that these classes be loaded when the class is resolved). This step happens in the loadClass( ) method.

If you want to use a custom class loader, the easiest route is to use the URL class loader. This limits the number of methods that you have to override.
To construct an instance of this class, use one of the following constructors:
public URLClassLoader(URL urls[])

```java
URL urls[] = new URL[2];
urls[0] = new URL("http://piccolo.East/~sdo/");
urls[1] = new URL("file:/home/classes/LocalClasses.jar"); ClassLoader parent = this.getClass().getClassLoader( ); URLClassLoader ucl = new URLClassLoader(urls, parent);


public final synchronized Class loadClass(String name, boolean resolve)
throws ClassNotFoundException {
// First check if we have permission to access the package.
SecurityManager sm = System.getSecurityManager( );
if (sm != null) {
int i = name.lastIndexOf('.');
if (i != −1) {
sm.checkPackageAccess(name.substring(0, i));
}
}
return super.loadClass(name, resolve);
}
```

6.3.4.2 Step 2: Use the previously−defined class, if available
The loadClass( ) method of the ClassLoader class performs this operation for you, which is why we've called the super.loadClass( ) method.

6.3.4.3 Step 3: Defer class loading to the parent
The loadClass( ) method of the ClassLoader class performs this operation. 6.3.4.4 Step 4: Optionally call the checkPackageDefinition( ) method
In order to call the checkPackageDefinition( ) method, you must override the findClass( ) method:

```java
protected Class findClass(final String name)
throws ClassNotFoundException {
// First check if we have permission to access the package. SecurityManager sm = System.getSecurityManager( );
if (sm != null) {
int i = name.lastIndexOf('.');
if (i != −1) {
sm.checkPackageDefinition(name.substring(0, i));
}
}
return super.findClass(name);
}
```

6.3.4.5 Step 5: Read in the class bytes
The URL class loader performs this operation for you by consulting the URLs that were passed to its constructor. If you need to adjust the way in which the class bytes are read, you should use the SecureClassLoader class instead.
6.3.4.6 Step 6: Create the appropriate protection domain
The URL class loader will create a code source for each class based on the URL from which the class was loaded and the signers (if any) of the class. The permissions associated with this code source will be obtained by using the getPermissions( ) method of the Policy class, which by default will return the permissions read in from the active policy files. In addition, the URL class loader will add additional permissions to that set:
If the URL has a file protocol, it must specify a file permission that allows all files that descend from the URL path to be read. For example, if the URL is file:///xyz/classes/, then a file permission with a name of /xyz/classes/− and an action list of read will be added to the set of permiss ions. If the URL is a jar file (file:///xyz/MyApp.jar), the name file permission will be the URL itself.
If you want to associate different permissions with the class, then you should override the getPermissions( ) method. For example, if we wanted the above rules to apply and also allow the class to exit the virtual machine, we'd use this code:
```java
protected PermissionCollection getPermissions(CodeSource codesource) { PermissionCollection pc = super.getPermissions(codesource);
pc.add(new RuntimePermission("exitVM"));
return pc;
}
```
We could completely change the permissions associated with the class (bypassing the Policy class altogether) by constructing a new permission collection in this method rather than calling super.getPermissions( ). The URL class loader will use whatever permissions are returned from this getPermissions( ) method to define the protection domain that will be associated with the class.
If you need to load bytes from a source that is not a URL (or from a URL for which you don't have a protocol handler, like FTP), then you'll need to extend the SecureClassLoader class. A subclass is required because the constructors of this class are protected, and in any case you need to override the findClass( )
 
The steps to use this class are exactly like the steps for the URLClassLoader class, except for step 5. To implement step 5, you must override the findClass( ) method like this:

```java
protected Class findClass(final String name) throws ClassNotFoundException {
// First check if we have permission to access the package.
// You could remove these 7 lines to skip the optional step 4.
SecurityManager sm = System.getSecurityManager( );
if (sm != null) {
int i = name.lastIndexOf('.');
if (i != −1) {
sm.checkPackageDefinition(name.substring(0, i));
}
}
// Now read in the bytes and define the class
try {
return (Class)
AccessController.doPrivileged(
new PrivilegedExceptionAction( ) {
public Object run( ) throws ClassNotFoundException {
byte[] buf = null;
try {
// Acutally load the class bytes
buf = readClassBytes(name);
} catch (Exception e) {
throw new ClassNotFoundException(name, e);
}
// Create an appropriate code source
CodeSource cs = getCodeSource(name);
// Define the class
return defineClass(name, buf,
0, buf.length, cs);
}
}
);
} catch (java.security.PrivilegedActionException pae) { throw (ClassNotFoundException) pae.getException( ); }
```



The syntax of this method is complicated by the fact that we need to load the class bytes in a privileged block. Depending on your circumstances, that isn't strictly necessary, but it's by far the most common case for class loaders. Say that your class loader loads class A from the database; that class is given minimal permissions. When that class references class B, the class loader will be asked to load class B and class A will be on the stack. When it's time to load the new class bytes, we need to load them with the permissions of the class loader rather than the entire stack, which is why we use a privileged block.
Notwithstanding, the try block has three operations: it loads the class bytes, it defines a code source for that class, and it calls the defineClass( ) method to create the class. The first two of the opera tions are encapsulated in the readClassBytes( ) and getCodeSource( ) methods; these are methods that
you must implement.
Loading the class bytes is an operation left to the reader. The reason for providing your own class loader is that you want to read the class bytes in some special way; otherwise, you'd use the URLClassLoader class. The code source is another matter: we must determine a URL and a set of certificates that should be
associated with the class.
In a signed jar file, the certificates are read from the jar file and the URL is the location of the jar file. In Chapter 12, we'll show how to get the certificates from a standard jar file and construct the appropriate URLClassLoader class. The code source is another matter: we must determine a URL and a set of certificates that should be
associated with the class.
In a signed jar file, the certificates are read from the jar file and the URL is the location of the jar file. In Chapter 12, we'll show how to get the certificates from a standard jar file and construct the appropriate The defineClass( ) method will call back to the getPermissions( ) method in order to complete the definition of the protection domain for this class. And that's why the URL used to construct the code source can be arbitrary: when you write the getPermissions( ) method, just make sure that you understand what the URL actually is. In default usage, the URL would be used to find entries in the policy files, but since you're defining your own permissions anyway, the contents of the URL don't matter. What matters is that you follow a consistent convention between the definition of your getCodeSource( ) and findClass( ) methods.
Hence, possible implementations of the getPermissions( ) and getCodeSource( ) methods are as follows:
```java
protected CodeSource getCodeSource(String name) {
try {
return new CodeSource(new URL("file", "localhost", name),
null);
} catch (MalformedURLException mue) {
mue.printStackTrace( );
}
return null;
}
protected PermissionCollection getPermissions(CodeSource codesource) {
PermissionCollection pc = new Permissions( );
pc.add(new RuntimePermission("exitVM"));
return pc;
}
```
If you're reading the class bytes from, say, a database, it would be more useful if you could pass an arbitrary string to construct the code source. That doesn't work directly since the code source requires a URL but the file part of the URL can be any arbitrary string. In this case, we just use the class name.
Note that the getPermissions( ) method of the SecureClassLoader class does not add the additional permissions that the same method of the URLClassLoader class adds. As a result, we do not call the super.getPermissions( ) 

## Delegation
As we've mentioned, class loading follows a delegation model. This model permits a class loader to be instantiated with this constructor:
protected ClassLoader(ClassLoader parent)
Create a class loader that is associated with the given class loader. This class loader delegates all operations to the parent first: if the parent is able to fulfill the operation, this class loader takes no action. For example, when the class loader is asked to load a class via the loadClass( ) method, it first calls the loadClass( ) method of the parent. If that succeeds, the class returned by the delegate will ultimately be returned by this class. If that fails, the class loader then uses its original logic to complete its task, something like this:
```java
public Class loadClass(String name) {
Class cl;
cl = delegate.loadClass(name);
if (cl != null)
return cl;
// else continue with the loadClass( ) logic
}
```
You may retrieve the delegate associated with a class loader with the following method
 public final ClassLoader getParent( )
Return the class loader to which operations are being delegated.
The class loader that exists at the root of the class loader hierarchy is retrieved via this method:
Return the system class loader (the class loader that was used to load the base application classes). If a security manager is in place, you must have the getClassLoader runtime permission to use this method.

## Loading Resources
A class loader can load not only classes, but any arbitrary resource: an audio file, an image file, or anything else. Instead of calling the loadClass( ) method, a resource is obtained by invoking one of these methods:
public URL getResource(String name)
public InputStream getResourceAsStream(String name)
The getResource( ) method calls the getSystemResource( ) method; if it does not find a system resource, it returns the object retrieved by a call to the findResource( ) method (which by default will be null). The getResourceAsStream( ) method simply


## Loading Libraries
Loading classes with native methods creates a call to this method of the ClassLoader class:
protected String findLibrary(String libname)
Return the directory from which native libraries should be loaded.
This method is used by the System.loadLibrary( ) method to determine the directory in which the native library in question should be found. If this method returns null (the default), the native library must be in one of the di


谈到常量池，在Java体系中，共用三种常量池。分别是字符串常量池、Class常量池和运行时常量池。
