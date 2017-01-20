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
- 


# Reference 
- http://javarevisited.blogspot.in/2012/07/countdownlatch-example-in-java.html
