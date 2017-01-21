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


# ThreadLocal
- ThreadLocal in Java is another way to achieve thread-safety **apart from writing immutable** classes.
- ThreadLocal in Java is a different way to achieve thread-safety, it doesn't address synchronization requirement, instead it eliminates sharing by providing explicitly copy of Object to each thread.
- Since Object is no more shared there is no requirement of Synchronization which can improve scalability and performance of application.
- One of the classic example of ThreadLocal is sharing SimpleDateForamt. Since SimpleDateFormat is not thread safe, having a global formatter may not work but having per Thread formatter will certainly work. but it can **be source of severe memory leak** and java.lang.OutOfMemoryError if not used carefully. so avoid until you don't have any other option.


# Reference 
- http://javarevisited.blogspot.in/2012/07/countdownlatch-example-in-java.html
- http://javarevisited.blogspot.sg/2012/05/how-to-use-threadlocal-in-java-benefits.html
- http://javarevisited.blogspot.com/2012/03/simpledateformat-in-java-is-not-thread.html
