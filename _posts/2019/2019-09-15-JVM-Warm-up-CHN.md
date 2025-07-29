---
title: JVM热身
weight: 500
date: 2020-09-15
tags:
- JVM预热
- Java
- 低延迟
layout: posts
---
> 此文是作者英文原文的翻译文章，英文原文在：http://todzhang.com/posts/2018-06-10-jvm-warm-up/

# JVM预热
“低延迟”的Java虚拟机应用在一些应用场景下是对系统至关重要对一个指标。比如说在`外汇交易系统`等金融业核心系统中。此文就是探讨一下如何运用Java虚拟机`预热`来提高系统效率。

`优化几调整JVM中每个进程过程称为预热`
请记住，对于低延迟的应用程序，我们需要预**先缓存所有类**-以便在运行时访问它们时立即可用。


# 逃逸分析

逃逸分析是Java Hotspot Server编译器可以用来分析新对象使用范围并决定是否在Java堆上分配它的一种技术。
根据逃逸分析，对象的转义状态可能是以下之一：
* GlobalEscape –对象转义方法和线程。例如，对象存储在静态字段中，或者存储在转义对象的字段中，或者作为当前方法的结果返回。

* ArgEscape –作为参数传递或由参数引用但在调用过程中不会全局转义的对象。通过分析被调用方法的字节码确定此状态。

* NoEscape –标量可替换对象，意味着可以从生成的代码中删除其分配。



经过逃逸分析后，服务器编译器从生成的代码中消除了标量可替换对象分配和关联的锁。服务器编译器还消除了对所有非全局转义对象的锁定。它不会用非全局转义对象的堆栈分配替换堆分配。

JIT积极地内联方法，从而消除了方法调用的开销。可以内联的方法包括静态，私有或最终方法，但如果可以确定它们没有被覆盖，则还可以包括公共方法。因此，后续的类加载可能会使先前生成的代码无效。因为在每个地方对每个方法进行内联都会花费时间，并且会生成不合理的大二进制文件，所以JIT编译器首先对热方法进行内联，直到达到阈值为止。为了确定哪些方法是热门的，JVM会保留计数器以查看方法被调用了多少次以及已执行了多少次循环迭代。这意味着内联仅在达到稳定状态后才发生，因此您需要重复进行一定次数的操作，然后才能有足够的概要分析信息供JIT编译器执行其工作。

您可以尝试打开Java命令行标志来窥视正在发生的事情，而不必试图猜测JIT在做什么：-XX：+ PrintCompilation -XX：+ UnlockDiagnosticVMOptions -XX：+ PrintInlining
这是他们的工作：
```bash
   -XX：+ PrintCompilation：JIT编译发生时记录
   -XX：+ UnlockDiagnosticVMOptions：启用其他标志，例如-XX：+ PrintInlining
```

GlobalEscape和ArgEscape对象必须在堆上分配，但是对于ArgEscape对象，可以删除一些锁定和内存同步开销，因为这些对象仅在调用线程中可见。

NoEscape对象可以自由分配，例如在堆栈上而不是堆上。实际上，在某些情况下，甚至根本不需要构造一个对象，而是仅构造该对象的标量值，例如对象Integer的int。同步也可能会被删除，因为我们知道只有这个线程会使用对象。例如，如果我们使用有些古老的StringBuffer（与StringBuilder相反，它具有同步方法），则可以安全地删除这些同步。

EA当前仅在C2 HotSpot编译器下可用，因此我们必须确保以-server模式运行。

## 为什么重要
从理论上讲，可以使用EA将NoEscape对象对象分配在堆栈上，甚至可以分配给CPU寄存器，从而可以非常快速地执行。

当我们在堆上分配对象时，我们开始消耗CPU缓存，因为对象被放置在堆上的不同地址上，彼此之间可能相距很远。这样，我们将快速耗尽L1 CPU缓存，并且性能会下降。另一方面，通过EA和堆栈分配，我们正在使用（很可能）已经在L1高速缓存中的内存。因此，EA和堆栈分配将改善我们的数据本地化。从性能的角度来看，这是很好的。

显然，当我们使用带有堆栈分配的EA时，垃圾收集的运行频率要低得多。这也许是最大的性能优势。回想一下，每次JVM运行一次完整的堆扫描时，我们都会从我们的CPU中获取性能，并且CPU高速缓存将很快耗尽。更不用说我们是否在服务器上调出了虚拟内存，从而导致GC破坏了性能。

EA的最重要优势不是性能。 EA允许我们使用Lambda，函数，流，迭代器等局部抽象，而不会造成任何明显的性能损失，从而使我们可以编写更好，更易读的代码。描述我们在做什么而不是如何完成的代码。

GC清理堆，而不是栈。当方法返回其调用方时，堆栈会自动清理，从而将堆栈指针重置为其以前的值。因此，GC将在执行EA / C2编译之前清理最终在堆栈中的对象。实际实例（或更确切地说，它们的相应表示形式）位于堆栈上，在EA优化的上下文中，堆栈上没有引用的对象。

# JIT优化

## 一些JIT编译技术
内联是Java HotSpot VM使用的最常见的JIT编译技术之一，它是将方法的主体替换为调用该方法的位置的实践。内联节省了调用方法的成本；无需创建新的堆栈框架。默认情况下，Java HotSpot VM将尝试内联包含少于35个字节JVM字节码的方法。

Java HotSpot VM进行的另一种常见优化是单态调度，它依赖于观察到的事实，即通常情况下，没有一种方法会导致对象引用在大多数情况下属于一种类型，而在另一种类型中却存在另一种类型的路径。次。

您可能会认为Java的静态类型会排除通过不同代码路径具有不同类型的情况，但是请记住，子类型的实例始终是超类型的有效实例（在Barbara Liskov之后，该原理称为Liskov替换原理）。这种情况意味着方法可能有两条路径（例如，一条路径传递一个超类型的实例，而一条路径传递一个子类型的实例），这在Java的静态类型定义中是合法的（并且确实会在实践）。

但是，在通常情况下（单态情况），不会发生具有不同的依赖于路径的类型。因此，我们知道在传递的对象上调用方法时将调用的确切方法定义，因为我们无需检查实际上使用了哪个替代。这意味着我们可以消除执行虚拟方法查找的开销，因此JIT编译器可以发出优化的机器代码，通常比等效的C ++调用要快（因为在C ++情况下，无法轻松消除虚拟查找）。

两种Java HotSpot VM编译器模式使用不同的JIT编译技术，并且对于相同的Java方法，它们可以输出非常不同的机器代码。但是，现代Java应用程序通常可以同时使用两种编译模式。

Java HotSpot VM使用许多其他技术来优化JIT编译生成的代码。循环优化，类型锐化，死代码消除和内在函数只是Java HotSpot VM尝试尽可能多地优化代码的其他方式。技术通常是一层一层地放在另一层之上，因此一旦应用了一种优化，编译器便可能能够看到更多可以执行的优化。

# 编译模式

在Java HotSpot VM内部，实际上有两个单独的JIT编译器模式，分别称为C1和C2。 C1用于需要快速启动和坚如磐石的优化的应用； GUI应用程序通常是此编译器的理想选择。另一方面，C2最初是用于长时间运行的（主要是服务器端）应用程序。在某些Java SE 7更高版本之前，分别使用-client和-server开关可以使用这两种模式。

两种编译器模式使用不同的技术进行JIT编译，并且对于相同的Java方法，它们可以输出非常不同的机器代码。但是，现代Java应用程序通常可以同时使用两种编译模式。为了利用这一事实，从某些Java SE 7更高版本开始，提供了称为分层编译的新功能。此功能在开始时使用C1编译器模式以提供更好的启动性能。一旦对应用程序进行了适当的预热，C2编译器模式将接管其工作，以提供更具攻击性的优化，并且通常提供更好的性能。随着Java SE 8的到来，分层编译现已成为默认行为。

# Java内存监视工具

```bash
pemi$ jps | grep Main
50903 Main
pemi$ jmap -histo 50903 | head
 num     #instances         #bytes  class name

----------------------------------------------
   1:            95       42952184  [I
   2:          1079         101120  [C
   3:           485          55272  java.lang.Class
   4:           526          25936  [Ljava.lang.Object;
   5:            13          25664  [B
   6:          1057          25368  java.lang.String
   7:            74           5328  java.lang.reflect.Field
```


## jmap-内存映射

工具或选项的说明和用法
Java任务控制
  
## Java Mission Control（JMC）
是用于HotSpot JVM的新JDK分析和诊断工具平台。它是一个具有高性能的工具套件，用于基本的监视，管理和生产时间分析以及诊断。 Java Mission Control最大限度地减少了性能分析开销，而性能开销通常是性能分析工具遇到的问题。请参阅Java Mission Control。
## jcmd实用程序
  
jcmd实用程序用于将诊断命令请求发送到JVM，这些请求对于控制Java Flight Records很有用。 JFR用于通过飞行记录事件对JVM和Java应用程序进行故障排除和诊断。请参见jcmd实用程序。
## Java VisualVM
  
该实用程序提供了一个可视界面，用于在Java应用程序在Java虚拟机上运行时查看有关Java应用程序的详细信息。此信息可用于对本地和远程应用程序进行故障排除，以及对本地应用程序进行性能分析。请参阅Java VisualVM。
JConsole实用程序
  
该实用程序是基于Java管理扩展（JMX）的监视工具。该工具使用Java虚拟机中的内置JMX工具来提供有关正在运行的应用程序的性能和资源消耗的信息。请参见JConsole。
jmap实用程序
  
该实用程序可以从Java进程，核心文件或远程调试服务器获取内存映射信息，包括堆直方图。请参阅jmap实用程序。
jps实用程序
  
该实用程序列出了目标系统上已检测到的Java HotSpot VM。该实用程序在嵌入式VM的环境中非常有用，也就是说，它是使用JNI Invocation API而不是Java启动器启动的。请参阅jps实用程序。
jstack实用程序
  
该实用程序可以从Java进程获取Java和本机堆栈信息。在Oracle Solaris和Linux操作系统上，该实用程序可以从核心文件或远程调试服务器中获取信息。请参阅jstack实用程序。
jstat实用程序
  
该实用程序使用Java中的内置工具来提供有关正在运行的应用程序的性能和资源消耗的信息。诊断性能问题（尤其是与堆大小和垃圾回收相关的问题）时可以使用该工具。请参见jstat实用程序。
jstatd守护程序
  
该工具是一个远程方法调用（RMI）服务器应用程序，它监视已检测Java虚拟机的创建和终止，并提供一个接口，以允许远程监视工具连接到在本地主机上运行的VM。请参见jstatd守护程序。
visualgc实用程序
  
该实用程序提供了垃圾收集系统的图形视图。与jstat一样，它使用Java HotSpot VM的内置工具。请参阅visualgc工具。
本机工具

```bash
$ jps
16217 MyApplication
16342 jps

The utility lists the virtual machines for which the user has access rights. This is determined by access-control mechanisms specific to the operating system. On Oracle Solaris operating system, for example, if a non-root user executes the jps utility, then the output is a list of the virtual machines that were started with that user's uid.

In addition to listing the PID, the utility provides options to output the arguments passed to the application's main method, the complete list of VM arguments, and the full package name of the application's main class. The jps utility can also list processes on a remote system if the remote system is running the jstatd daemon.

```

# 无GC的Java
没有GC的Java开发
Coral Blocks开发的所有产品都具有非常重要的功能，可以将零垃圾抛在后面。由于Java垃圾收集器（即GC）施加的延迟对于高性能系统是不可接受的，并且由于无法关闭GC，因此Java实时系统的最佳选择是根本不产生任何垃圾。想象一下，GC永远不会启动。想象一下一个高性能匹配引擎，其运行时间为微秒级，每秒发送和接收数十万条消息。如果GC在任何给定时间决定以1毫秒以上的延迟开始运行，则系统中的中断将是巨大的。因此，如果要使用Java开发具有最小方差和延迟的实时系统，最好的选择是正确执行此操作，而不会为GC创建任何垃圾。

## 热身，检查GC和采样
确保您的系统不产生任何垃圾的关键是从开始到完成数百万次预热您的关键路径，然后再检查数百万次内存分配。如果它随着迭代次数的增加而线性地分配内存，则很可能会产生垃圾，您应该使用堆栈跟踪

--end--
