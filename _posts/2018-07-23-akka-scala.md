---
title: akka framework of scala
layout: posts
---

# philosophy
The actor model adopts the philosophy that everything is an actor. This is similar to the everything is an object philosophy used by some object-oriented programming languages.


Decoupling the sender from communications sent was a fundamental advance of the Actor model enabling asynchronous communication and control structures as patterns of passing messages.


Recipients of messages are identified by address, sometimes called "mailing address". Thus an actor can only communicate with actors whose addresses it has.

# Route
Routes effectively are simply highly specialised functions that take a RequestContext and eventually complete it, which could (and often should) happen asynchronously.

Directives create Routes.

The Route is the central concept of Akka HTTP's Routing DSL. All the structures you build with the DSL, no matter whether they consists of a single line or span several hundred lines, are type turning a RequestContext into a Future[RouteResult].

```scala
type Route = RequestContext => Future[RouteResult]
```


Generally when a route receives a request (or rather a RequestContext for it) it can do one of these things:

- Complete the request by returning the value of requestContext.complete(...)
- Reject the request by returning the value of requestContext.reject(...) (see Rejections)
- Fail the request by returning the value of requestContext.fail(...) or by just throwing an exception (see Exception Handling)
- Do any kind of asynchronous processing and instantly return a Future[RouteResult] to be eventually completed later

## The Routing Tree
Essentially, when you combine directives and custom routes via nesting and the ~ operator, you build a routing structure that forms a tree. When a request comes in it is injected into this tree at the root and flows down through all the branches in a depth-first manner until either some node completes it or it is fully rejected.

In RouteDirective.scala

```scala
/**
   * Completes the request using the given arguments.
   *
   * @group route
   */
  def complete(m: ? ToResponseMarshallable): StandardRoute =
    StandardRoute(_.complete(m))

```


## RouteResult
RouteResult is a simple abstract data type (ADT) that models the possible non-error results of a Route. It is defined as such:
```scala
sealed trait RouteResult

object RouteResult {
  final case class Complete(response: HttpResponse) extends RouteResult
  final case class Rejected(rejections: immutable.Seq[Rejection]) extends RouteResult
}
```


## Routing DSL

In addition to the Core Server API Akka HTTP provides a very flexible ,Routing DSL, for elegantly defining RESTful web services.

Http().bindAndHandle(routes ~ abcRoute, host, port)

```scala
/**
     * Returns a Route that chains two Routes. If the first Route rejects the request the second route is given a
     * chance to act upon the request.
     */
    def ~(other: Route): Route = { ctx ?
      import ctx.executionContext
      route(ctx).fast.flatMap {
        case x: RouteResult.Complete ? FastFuture.successful(x)
        case RouteResult.Rejected(outerRejections) ?
          other(ctx).fast.map {
            case x: RouteResult.Complete               ? x
            case RouteResult.Rejected(innerRejections) ? RouteResult.Rejected(outerRejections ++ innerRejections)
          }
      }
    }

```

### Path matching
> Note
The path matching DSL describes what paths to accept after URL decoding. This is why the path-separating slashes have special status and cannot simply be specified as part of a string! The string ¡°foo/bar¡± would match the raw URI path ¡°foo%2Fbar¡±, which is most likely not what you want!



# Sink
A Sink is a set of stream processing steps that has one open input. Can be used as a Subscriber

# supervision

## What Supervision Means
As described in Actor Systems supervision describes a dependency relationship between actors: the supervisor delegates tasks to subordinates and therefore must respond to their failures. When a subordinate detects a failure (i.e. throws an exception), it suspends itself and all its subordinates and sends a message to its supervisor, signaling failure. Depending on the nature of the work to be supervised and the nature of the failure, the supervisor has a choice of the following four options:

- Resume the subordinate, keeping its accumulated internal state
- Restart the subordinate, clearing out its accumulated internal state
- Stop the subordinate permanently
- Escalate the failure, thereby failing itself


## sealed class
```java
object Supervision {
  sealed trait Directive
}
```
A sealed class may not be directly inherited, except if the inheriting template is defined in the same source file as the inherited class. However, subclasses of a sealed class can inherited anywhere.

## implicit
A method can have an implicit parameter list, marked by the implicit keyword at the start of the parameter list. If the parameters in that parameter list are not passed as usual, Scala will look if it can get an implicit value of the correct type, and if it can, pass it automatically.

The places Scala will look for these parameters fall into two categories:

Scala will first look for implicit definitions and implicit parameters that can be accessed directly (without a prefix) at the point the method with the implicit parameter block is called.
Then it looks for members marked implicit in all the companion objects associated with the implicit candidate type.

## KillSwitch
A KillSwitch allows completion of Graphs from the outside by completing Graphs of FlowShape linked to the switch. Depending on whether the KillSwitch is a UniqueKillSwitch or a SharedKillSwitch one or multiple streams might be linked with the switch.

```scala
trait KillSwitch {
//After calling KillSwitch.shutdown() the linked Graphs of FlowShape are completed normally.
 def shutdown(): Unit
 def abort(ex:Throwable): Unit
}
```

## Source
A Source is a set of stream processing steps that has one open output. It can comprise any number of internal sources and transformations that are wired together, or it can be an atomic source, e.g. from a collection or a file. Materialization turns a Source into a Reactive Streams Publisher (at least conceptually).


### connect to Sink
```scala
/**
   * Connect this [[akka.stream.scaladsl.Source]] to a [[akka.stream.scaladsl.Sink]],
   * concatenating the processing steps of both.
   */
  def to[Mat2](sink: Graph[SinkShape[Out], Mat2]): RunnableGraph[Mat] = toMat(sink)(Keep.left)
```



# Future
trait Future[+T]
 extends Awaitable[T]
A Future represents a value which may or may not *currently* be available, but will be available at some point, or an exception if that value could not be made available. Asynchronous computations that yield futures are created with the Future.apply call and are computed using a supplied ExecutionContext, which can be backed by a Thread pool.
  
   import ExecutionContext.Implicits.global
   val s = "Hello"
   val f: Future[String] = Future {
     s + " future!"
   }
   f foreach {
     msg => println(msg)
   }

## Future introduction
Futures provide a way to reason about performing many operations in parallel¨C in an efficient and non-blocking way. A Future is a placeholder object for a value that may not yet exist. Generally, the value of the Future is supplied concurrently and can subsequently be used. Composing concurrent tasks in this way tends to result in faster, asynchronous, non-blocking parallel code.

By default, futures and promises are non-blocking, making use of callbacks instead of typical blocking operations. To simplify the use of callbacks both syntactically and conceptually, Scala provides combinators such as flatMap, foreach, and filter used to compose futures in a non-blocking way. Blocking is still possible - for cases where it is absolutely necessary, futures can be blocked on (although this is discouraged).



# Scala scope protection:
private[C] means that access is private "up to" C, where C is the corresponding package, class or singleton object.
```scala
private[http] def build = {
  // ...
}
```

The modi?er can be quali?ed with an identi?er C (e.g. private[C]) that must denote a class or package enclosing the de?nition. Members labeled with such a modi?er are accessible respectively only from code inside the package C or only from code inside the class C and its companion module (¡ì5.4). Such members are also inherited only from templates inside C.



# Scala flexible import
you can import several classes the Scala way:
```scala
import java.io.{File, IOException, FileNotFoundException}
```
Use the following syntax to import everything from the java.io package:
```scala
import java.io._
```
The _ character in this example is similar to the * wildcard character in Java.

If the _ character feels unusual at first, it helps to know that it¡¯s used consistently throughout the Scala language as a wildcard character, and that consistency is very nice.



## Directives
A ¡°Directive¡± is a small building block used for creating arbitrarily complex route structures. Akka HTTP already pre-defines a large number of directives and you can easily construct your own:



# Regular Expression
```scala
val pattern = "Scala".r
      val str = "Scala is Scalable and cool"
      
      println(pattern findFirstIn str)

```

We create a String and call the r( ) method on it. Scala implicitly converts the String to a RichString and invokes that method to get an instance of Regex. To find a first match of the regular expression, simply call the findFirstIn() method. If instead of finding only the first occurrence we would like to find all occurrences of the matching word, we can use the findAllIn( ) method and in case there are multiple Scala words available in the target string, this will return a collection of all matching words.

## PathMatcher

- Segment: PathMatcher1[String]
Matches if the unmatched path starts with a path segment (i.e. not a slash). If so the path segment is extracted as a String instance.



# Option
In short, if you have a value of type A that may be absent, Scala uses an instance of Option[A] as its container. An Intance of Option is either an instance of case class Some when it is present or case object None when it is not. Since both Some and None are children of Option, your function signature should declare that the returned value is an Option of some type, e.g. Option[A]

## Sample
It is very easy to create an Option in Scala, i.e. you can use a present/absent value directly.
```scala
val optionalInt: Option[Int] = Some(1)
// or
// val optionalInt: Option[Int] = None
```

### To validate user login
```scala
def auth(user:String, pwd:String): AuthResult =
	(user, pwd) match {
	case (u, _) if Option(u).exists(_.trim.isEmpty) => ErrorLogin
	case (_, p) if Option(p).exists(_.trim.isEmpty) => ErrorPwd
	case (u, p) => doAuth(u,p)

}
```
## isDefined
you add a checker for the None value using the isDefined method and specify logic to handle each scenario accordingly.

```scala
def addTwoWithDefault(a: Option[Int]): Int = {
  if(a.isDefined) a.get + 2 else 2
}
```

## getOrElse

In many cases, you have a fallback or default value for your absent values, e.g. zero in the above example. With Option, you can easily provide a default value via the getOrElse method.

def addTwoWithDefault(a: Option[Int]): Int = a.getOrElse(0) + 2

## flatten
Assume that we have a List of Option[Int].
```scala
val l: List[Option[Int]] = List(Some(3), Some(1), None, Some(5), Some(8), None)
```

A common scenario is that we need to filter out the absent values and return a List of Int. A straightfoward approach is to combine filter with .isDefined.

```scala
l.filter(_.isDefined).map(_.get) 
// res1: List[Int] = List(3, 1, 5, 8)
```
However, Scala actually provides an elegent built-in function to achieve the same goal, which is often more preferred.

```scala
l.flatten
// res1: List[Int] = List(3, 1, 5, 8)
```


# underscore
In Scala, pattern matching is somewhat similar to java switch statement. But it is more powerful.

```scala
 def matchTest(x: Int): String = x match {
    case 1 => "one"
    case 2 => "two"
    case _ => "anything other than one and two"
  }

```

_ acts like a wildcard. It will match anything. Scala allows nested patterns, so we can nest the _ also.Lets see another example that uses _ in nested pattern.

```scala
expr match {
  case List(1,_,_) => " a list with three element and the first element is 1"
  case List(_*)  => " a list with zero or more elements "
  case Map[_,_] => " matches a map with any key type and any value type "
  case _ =>
  }
```

## Anonymous Functions
Scala represents anonymous functions with a elegant syntax. The _ acts as a placeholder for parameters in the anonymous function. The _ should be used only once, But we can use two or more underscores to refer different parameters.

```scala
List(1,2,3,4,5).foreach(print(_))
List(1,2,3,4,5).foreach( a => print(a))
// Here the _ refers to the parameter. The first one is a short form of the second one. Lets look at another example which take two parameters.

val sum = List(1,2,3,4,5).reduceLeft(_+_)
val sum = List(1,2,3,4,5).reduceLeft((a, b) => a + b)
```

## Functions
Scala is a functional language. So we can treat function as a normal variable. If you try to assign a function to a new variable, the function will be invoked and the result will be assigned to the variable. This confusion occurs due to the optional braces for method invocation. We should use _ after the function name to assign it to another variable.

```scala
List(1,2,3,4,5).foreach(print(_))
class Test {
  def fun = {
    // some code
  }
  val funLike = fun _
}
List(1,2,3,4,5).foreach(print(_))
```



# Either, Left, Right

Using Either, Left, and Right
Prior to Scala 2.10, an approach similar to Try was available with the Either, Left, and Right classes. With these classes, Either is analogous to Try, Right is similar to Success, and Left is similar to Failure.

The following method demonstrates how to implement the Either approach:

```scala
def divideXByY(x: Int, y: Int): Either[String, Int] = {
    if (y == 0) Left("Dude, can't divide by 0")
    else Right(x / y)
}
```
As shown, your method should be declared to return an Either, and the method body should return a Right on success and a Left on failure. The Right type is the type your method returns when it runs successfully (an Int in this case), and the Left type is typically a String, because that¡¯s how the error message is returned.

As with Option and Try, a method returning an Either can be called in a variety of ways, including getOrElse or a match expression:


```scala
val x = divideXByY(1, 1).right.getOrElse(0)   // returns 1
val x = divideXByY(1, 0).right.getOrElse(0)   // returns 0

// prints "Answer: Dude, can't divide by 0"
divideXByY(1, 0) match {
    case Left(s) => println("Answer: " + s)
    case Right(i) => println("Answer: " + i)
}
```
You can also access the error message by testing the result with isLeft, and then accessing the left value, but this isn¡¯t really the Scala way:

```scala
scala> val x = divideXByY(1, 0)
x: Either[String,Int] = Left(Dude, can't divide by 0)

scala> x.isLeft
res0: Boolean = true

scala> x.left
res1: scala.util.Either.LeftProjection[String,Int] =
      LeftProjection(Left(Dude, can't divide by 0))
```
Although the Either classes offered a potential solution prior to Scala 2.10, I now use the Try classes in all of my code instead of Either.


### classOf
Retrieve the runtime representation of a class type. classOf[T] is equivalent to the class literal T.class in Java.

## Operators
// Keywords
<-  // Used on for-comprehensions, to separate pattern from generator
=>  // Used for function types, function literals and import renaming


# Akka framework
Akka is a toolkit and runtime for building highly concurrent, distributed, and fault-tolerant event-driven applications on the JVM. 

Actors are the unit of execution in Akka. The Actor model is an abstraction that makes it easier to write correct concurrent, parallel and distributed systems.

This will get your feet wet, and hopefully inspire you to dive deeper into the wonderful sea of Akka!

The Akka team refers to their creation as a toolkit rather than a framework. Frameworks tend to be a mechanism for providing a discrete element of a stack (e.g. the ui, or the web services layer). Akka provides a set of tools to render any part of the stack, and to provide the interconnects between them. 

He two ways (shared mutable state/message passing (Akka)) to solve the problem of selling tickets.

Actors do not share state, can only communicate through immutable messages and do not talk to each other directly but through actor references, similar to the addresses we talked about. This approach satisfies the three things we wanted to change. So why is this simpler than the shared mutable state approach?
- We don't need to manage locks. We don't have to think about how to protect the shared data. Inside an actor we're safe.
- We are more protected from deadlocks caused by out of order access by multiple threads, that cause the system to wait forever, or other problems like race conditions and thread starvation. Use of Akka precludes most of these problems, relieving us of the burden.
- Performance tuning a shared mutable state solution is hard work and error prone and verification through tests is nearly impossible.

## Benefits of using the Actor Model

The following characteristics of Akka allow you to solve difficult concurrency and scalability challenges in an intuitive way:

- Event-driven model — Actors perform work in response to messages. Communication between Actors is asynchronous, allowing Actors to send messages and continue their own work without blocking to wait for a reply.
- Strong isolation principles — Unlike regular objects in Java, an Actor does not have a public API in terms of methods that you can invoke. Instead, its public API is defined through messages that the actor handles. This prevents any sharing of state between Actors; the only way to observe another actor’s state is by sending it a message asking for it.
- Location transparency — The system constructs Actors from a factory and returns references to the instances. Because location doesn’t matter, Actor instances can start, stop, move, and restart to scale up and down as well as recover from unexpected failures.
- Lightweight — Each instance consumes only a few hundred bytes, which realistically allows millions of concurrent Actors to exist in a single application.


### Message
two special channels. The first is the Dead Letter channel, which contain message that couldn't be delivered. This is sometimes also called a dead message queue. This channel can help when debugging, why some messages aren't processed or to monitor where there are problems.


### EventStream
the benefit of decoupling the receivers and the sender and the dynamic nature of the publish-subscribe channel, but because the EventStream is available for all actors is also a nice solution for messages which can be send from all over the system and needs to be collected at one or more Actors. A good example is logging. Logging can be done throughout the system and needs to be collected at one point and be written to a log file. Internally the ActorLogging is using the EventStream to collect the log lines from all over the system.

### Dead Letter Message
Akka is using the EventStream to implement the dead letter queue. This way only the actors which are interested in the failed messages are receiving them. When a message is queued in a mailbox of an actor that Terminates or is send after the Termination, the message is send to the EventStream of the ActorSystem. The message is wrapped into a DeadLetter object. This Object contains the original message, the sender of the message and the intended receiver. This way the Dead letter queue is integrated in the EventStream. To get these dead letter messages you only need to subscribe your actor to the EventStream with the DeadLetter class as the Classifier.


Messages send to a Terminated Actor can't be processed anymore and the ActorRef of this actor should not be used anymore. When there are messages send to a terminated Actor, these message will be send to the DeadLetter queue.

Another use of the DeadLetter queue is when the processing fails. This is a Actor specific decision. An actor can decide that a received message couldn't be processed and that it doesn't know what to do with it. In this situation the messages can be send to the dead letter queue. 

## Design recommendations
When defining Actors and their messages, keep these recommendations in mind:

- Since messages are the Actor’s public API, it is a good practice to define messages with good names and rich semantic and domain specific meaning, even if they just wrap your data type. This will make it easier to use, understand and debug actor-based systems.
- Messages should be immutable, since they are shared between different threads.
- It is a good practice to put an actor’s associated messages as static classes in the class of the Actor. This makes it easier to understand what type of messages the actor expects and handles.
- It is also a common pattern to use a static props method in the class of the Actor that describes how to construct the Actor.

### Props
The static props method creates and returns a Props instance. Props is a configuration class to specify options for the creation of actors, think of it as an immutable and thus freely shareable recipe for creating an actor that can include associated deployment information. This example simply passes the parameters that the Actor requires when being constructed. We will see the props method in action later in this tutorial.


## configuration

When using the default, the library will try to find the configuration file. Since the library supports a number of different configuration formats, it looks for different files, in the following order:
application.properties
This file should contain the configuration properties in the java property file format.
application.json
This file should contain the configuration properties in the json style

application.conf
This file should contain the configuration properties in the HOCON format. This is a format based on json but easier to read..
It is possible to use all the different files at the same time. For the example below, in listing 7.2 we use the last file:
MyAppl {
    version = 10
    description = "My application"
    database {
        connect="jdbc:mysql://localhost/mydata"
        user="me"
        }
}
Nesting is done by simply grouping with {}s

### substitution
 hostname="localhost"
hostname=${?HOST_NAME}
MyAppl {
    version = 10
    description = "My
    application"
    database {
        connect="jdbc:mysql://${hostname}/mydata"
user="me" }
}

define the variable first, if system environment do exist, override it, otherwise use default
? means get a variable from system envrionment

### Default/fallback properies
Default properties are configured in the file reference.conf and placed in the root of the jar file; the idea is that every library contains its own defaults. The configuration library will find all the reference.conf files and integrate these settings into the configuration fall-back structure. 

### Order of properties
System properties->application.conf->applicaiton.json->application.properties->reference.conf


## The power of location transparency

In Akka you can’t create an instance of an Actor using the new keyword. Instead, you create Actor instances using a factory. The factory does not return an actor instance, but a reference, akka.actor.ActorRef, that points to the actor instance. This level of indirection adds a lot of power and flexibility in a distributed system.

In Akka location doesn’t matter. Location transparency means that the ActorRef can, while retaining the same semantics, represent an instance of the running actor in-process or on a remote machine. If needed, the runtime can optimize the system by changing an Actor’s location or the entire application topology while it is running. This enables the “let it crash” model of failure management in which the system can heal itself by crashing faulty Actors and restarting healthy ones.

## The Akka ActorSystem

The akka.actor.ActorSystem factory is, to some extent, similar to Spring’s BeanFactory. It acts as a container for Actors and manages their life-cycles. The actorOf factory method creates Actors and takes two parameters, a configuration object called Props and a name.

### Asynchronous communication
Actors are reactive and message driven. An Actor doesn’t do anything until it receives a message. Actors communicate using asynchronous messages. This ensures that the sender does not stick around waiting for their message to be processed by the recipient. Instead, the sender puts the message in the recipient’s mailbox and is free to do other work. The Actor’s mailbox is essentially a message queue with ordering semantics. The order of multiple messages sent from the same Actor is preserved, but can be interleaved with messages sent by another Actor.


You might be wondering what the Actor is doing when it is not processing messages, i.e. doing actual work? It is in a suspended state in which it does not consume any resources apart from memory. Again, showing the lightweight, efficient nature of Actors.

### Sending messages to an Actor
To put a message into an Actor’s mailbox, use the tell method on the ActorRef. For example, the main class of Hello World sends messages to the Greeter Actor like this:

```java
howdyGreeter.tell(new WhoToGreet("Akka"), ActorRef.noSender());
howdyGreeter.tell(new Greet(), ActorRef.noSender());
```

The test class is using akka.test.javadsl.TestKit, which is a module for integration testing of actors and actor systems. This class only uses a fraction of the functionality provided by TestKit.

## Akka under the hood
So are there no concurrency primitives like locks used at all in Akka? Well, of course there are, it's just that you don't have to deal with them directly . Everything still eventually runs on threads and low level concurrency primitives. Akka uses the java.util.concurrent library to coordinate message processing and takes great care to minimize the number of locks used to an absolute bare minimum. It uses lock free and wait free algorithms where possible, for example compare-and-swap (CAS) techniques, which are beyond the scope of this book. And because nothing can be shared between actors, the shared locks that you would normally have between objects are not present at all. 



There are other benefits that stem from the message passing approach that Akka uses, which we will discuss in the next sections. We have touched on them briefly already:
1. Even in this first, simple example, the message passing approach is clearly more fault tolerant, averting catastrophic failure if one component (no matter how key) fails.
2. The shared mutable state is always in one place in the example (in one JVM if it is kept entirely in memory). If you need to scale beyond this constraint, you will have to (re)distribute the data somehow. Since the message passing style uses addresses, looking ahead, you can see that if local and remote addresses were interchangeable, scaling out would be possible without code changes of any kind.


This scenario is one example of a fault tolerance strategy that Akka provides, which is called the Restart strategy. Other strategies that can be used are Resume, Stop and Escalate. 

## Scale up and Scale out
In our Ticketing example, scaling up would mean getting more TicketingAgents running on our one server, scaling out would be bringing up TicketingAgents on a number of machines.


## Locking

locks result in contention, which will mean the number of threads doing work at any one time is often less than the total number, as some will have to wait on each other to finish. Sharing as little as possible means locking as little as possible, which is the goal of the message passing approach.

Every thread has a stack to store runtime data. The size of the stack differs per operating system, for instance on the linux x64 platform it is normally 256kB. The stack size is one of the factors that limits the number of threads that run at the same time on a server. Around 4096 threads can fit in 1GB of memory on the linux x64 platform.

## Dispatcher

Actors run on an abstraction which is called a dispatcher. The dispatcher takes care of which threading model is used and processes the mailboxes.

Actors are lightweight because they run on top of dispatchers, the actors are not necessarily directly proportional to the number of threads. Akka Actors take a lot less space than threads, around 2.7 million actors can fit in 1GB of memory. A big difference compared to 4096 threads, which means that you can create different types of actors more freely than you would when using threads directly. There are different types of dispatchers to choose from which can be tuned to specific needs.

We identified that we had to make the following changes to get to a message passing style:
1. No mutable shared data structure. 
2. Immutable message passing.
3. Asynchronous message sending.


Akka implements actors and which components compare to the concepts we've talked about so far: actors, addresses and mailboxes.

## Actor Path
So how do you get an actor reference to an actor in the hierarchy? This is where ActorPaths come in. You could compare the hierarchy of actors to a URL path structure. Every actor has a name. This name needs to be unique per level in the hierarchy, two sibling actors cannot have the same name (if you do not provide a name Akka generates one for you, but it is a good idea to name all your actors). All actor references can be located directly by an actor path, absolute or relative, and it has to follow the URI generic syntax. An actor path is built just like a URI, starting with a scheme followed by a scheme-specific part,


## Core Actor Operations
Another way to look at an actor is to describe the operations that it supports. An Akka actor has four core operations :
1. CREATE: An actor can create another actor. In Akka, actors are part of an actor system, which defines the root of the actor hierarchy and creates top-level actors. Every actor can create child actors. The topology of the actors is dynamic, it depends on which actors create other actors and which addresses are used to communicate with them.
2. SEND: An actor can send a message to another actor. Messages are sent asynchronously, using an address to send to an Actor associated with a given Mailbox.
3. BECOME: The behavior of an actor can be dynamically changed. Messages are received one at a time and an actor can designate that it wants to handle next messages in a different way, basically swapping its behavior, which we will look at in later chapters.
4. SUPERVISE: An actor supervises and monitors its children in the actor hierarchy and manages the failures that happen. As we will see in chapter 3, this provides a clean separation between message processing and error handling.

## Akka concurrency
Message passing enables an easier road to real concurrency
 With that concurrent approach, we will be able to scale up and out
We can scale both the request and the processing elements of our application
Messages also unlock greater fault tolerance capabilities
Supervision provides a means of modeling for both concurrency and fault tolerance
Akka infuses our code with these powers in a lightweight, unobtrusive manner

### Build Akka
using TypeSafe's Simple Build Tool (SBT) to create a single jar file that can be used to run the app

If you have not worked with the SBT DSL before it is important to note that you need to put en empty line between lines in the file (this is the price we pay for not telling Scala where each expression ends).


### tell vs ask
Messages are sent to an Actor through one of the following methods.

! means “fire-and-forget”, e.g. send a message asynchronously and return immediately. Also known as tell.

? sends a message asynchronously and returns a Future representing a possible reply. Also known as ask.

So below line is equivalent to tell
```scala
class ReceiveActor extends Actor {

  def receive = {
    case "Hello" => sender ! "And Hello to you!" // same as sender.tell("And Hello to you!")
  }
}
```
#### Sample of actor
```scala
package com.goticks
import akka.actor.{PoisonPill, Actor}
class TicketSeller extends Actor {
  import TicketProtocol._
  var tickets = Vector[Ticket]()
  def receive = {
    case GetEvents => sender ! tickets.size
    case Tickets(newTickets) =>
      tickets = tickets ++ newTickets
    case BuyTicket =>
      if (tickets.isEmpty) {
        sender ! SoldOut
        self ! PoisonPill
}
      tickets.headOption.foreach { ticket =>
        tickets = tickets.tail
        sender ! ticket
} }
}

case Event(name, nrOfTickets) =>
  if(context.child(name).isEmpty) {
If TicketSellers have not been
   val ticketSeller = context.actorOf(Props[TicketSeller], name)
  val tickets = Tickets((1 to nrOfTickets).map{
    nr=> Ticket(name, nr)).toList
}
  ticketSeller ! tickets
}
sender ! EventCreated

```

The BoxOffice creates TicketSellers for each event. Notice that it uses it's context instead of the actor system to create the actor; Actors created with the context of another Actor are its children and subject to the parent Actor's supervision


## Test
Right now it always fails since it is not implemented yet, as is expected in Red-Green-Refactor style, where you first make sure the test fails (Red), then implement the code to make it pass (Green), after which you might refactor the code to make it nicer.

## source code

### UntypedActor
This class is the Java cousin to the akka.actor.Actor Scala interface. Subclass this abstract class to create a MDB-style untyped actor.

An actor has a well-defined (non-cyclic) life-cycle.

    RUNNING (created and started actor) - can receive messages
    SHUTDOWN (when 'stop' or 'exit' is invoked) - can't do anything

The Actor's own akka.actor.ActorRef is available as getSelf(), the current message’s sender as getSender() and the akka.actor.UntypedActorContext as getContext(). The only abstract method is onReceive() which is invoked for each processed message unless dynamically overridden using getContext().become().

Annotations
    @Deprecated @deprecated 
Deprecated

    (Since version 2.5.0) Use AbstractActor instead of UntypedActor.

### loggingAdaptor
trait LoggingAdapter extends AnyRef

Logging wrapper to make nicer and optimize: provide template versions which evaluate .toString only if the log level is actually enabled. Typically used by obtaining an implementation from the Logging object:
