---
title: annoying-debug-logs-in-springboot-test
header:
    image: /assets/images/annoying-debug-logs-in-springboot-test.jpg
date: 2023-03-18
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/annoying-debug-logs-in-springboot-test
layout: single
category: tech
---

# Stop annoying debug logs in spring boot test


When you run the sperm boot testing and there are some dependency library for example, the hibernate will print out some logs there. There are some cases very annoying. This the hybrid print out too many locks which is in the debug level but actually already enabled the changed lock level to info or even higher, but still coming out to solve this problem. Actually you can do two stuff. The firstly is to change the application dot yam file, and the second is to change the um activation profile in your test case test class that is to explicitly to assign one file or profile to be used to load the properties

As below sample

![img.png](/assets/images/annoyying_hibernate.png)

## Solution
To add the following line in the application dot yam file

```yaml
logging:
  level:
    ROOT: INFO
    org:
      hibernate:
        SQL: INFO
        type: INFO
```
   
Adn add below in your test class

```java
@SpringBootTest(properties = ["spring.flyway.enabled=false"])
@ActiveProfiles("integration")
class MyClassTest {
```

## ConcurrentModificationException in threas join

```kotlin
   // wait for all threads to finish
        threads.forEach { it.join() }
```

Error message

```shell
Exception in thread "Thread-8" javax.persistence.RollbackException: Error while committing the transaction
	at org.hibernate.internal.ExceptionConverterImpl.convertCommitException(ExceptionConverterImpl.java:81)
	at org.hibernate.engine.transaction.internal.TransactionImpl.commit(TransactionImpl.java:104)
	at com.thinkchina.unifyxp2.controller.ShopperOrderCheckControllerConcurrentTest$testConcurrentLoadWithRandomUpdates$1.invoke(ShopperOrderCheckControllerConcurrentTest.kt:80)
	at com.thinkchina.unifyxp2.controller.ShopperOrderCheckControllerConcurrentTest$testConcurrentLoadWithRandomUpdates$1.invoke(ShopperOrderCheckControllerConcurrentTest.kt:75)
	at kotlin.concurrent.ThreadsKt$thread$thread$1.run(Thread.kt:30)
Caused by: java.util.ConcurrentModificationException
	at java.base/java.util.HashMap.forEach(HashMap.java:1340)
	at org.hibernate.resource.jdbc.internal.ResourceRegistryStandardImpl.releaseResources(ResourceRegistryStandardImpl.java:323)
	at org.hibernate.resource.jdbc.internal.AbstractLogicalConnectionImplementor.afterTransaction(AbstractLogicalConnectionImplementor.java:60)
	at org.hibernate.resource.jdbc.internal.LogicalConnectionManagedImpl.afterTransaction(LogicalConnectionManagedImpl.java:167)
	at org.hibernate.resource.jdbc.internal.LogicalConnectionManagedImpl.afterCompletion(LogicalConnectionManagedImpl.java:290)
	at org.hibernate.resource.jdbc.internal.AbstractLogicalConnectionImplementor.commit(AbstractLogicalConnectionImplementor.java:95)
	at org.hibernate.resource.transaction.backend.jdbc.internal.JdbcResourceLocalTransactionCoordinatorImpl$TransactionDriverControlImpl.commit(JdbcResourceLocalTransactionCoordinatorImpl.java:282)
	at org.hibernate.engine.transaction.internal.TransactionImpl.commit(TransactionImpl.java:101)
	... 3 more
```
    

--HTH--
