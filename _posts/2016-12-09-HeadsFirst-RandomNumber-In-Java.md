---
layout: posts
title: Random number in java
tags:
- MyBlog
- Java
---
ThreadLocalRandom, SecureRandm, java.util.Random, java.math.Random

Instances of java.util.Random are threadsafe. However, the concurrent use of the same java.util.Random instance across threads may encounter contention and consequent poor performance. Consider instead using ThreadLocalRandom in multithreaded designs. 

The Java Math library function Math.random() generates a double value in the range [0,1). Notice this range does not include the 1.

```java
int rand = ThreadLocalRandom.current().nextInt(x,y);
```

# Reference
- [How to generate a range of random integers in Java](http://www.javaguru.co/2014/12/how-to-generate-range-of-random.html)
- [Random JavaDoc](http://docs.oracle.com/javase/8/docs/api/java/util/Random.html)
- [SecureRandom JavaDoc](http://docs.oracle.com/javase/8/docs/api/java/security/SecureRandom.html)
- [ThreadLocalRandom JavaDoc](http://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ThreadLocalRandom.html)
- [Apache Common Math](http://commons.apache.org/proper/commons-math/)
- [LCG wikipedia](https://en.wikipedia.org/wiki/Linear_congruential_generator)
- [Blog about this topic](http://www.programering.com/a/MDN1ETMwATM.html)
- [ImportNew](http://www.importnew.com/12460.html)
