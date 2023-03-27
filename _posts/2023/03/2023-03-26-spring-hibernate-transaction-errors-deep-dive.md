---
title: Spring Hibernate Transaction Errors Deep Dive
header:
    image: /assets/images/GoogleMap_missing_JPN.jpg
date: 2023-03-26
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/spring-hibernate-transaction-errors-deep-dive
layout: single
category: tech
---
# what's spring boot test annotation

```java
org.springframework.transaction.UnexpectedRollbackException: Transaction silently rolled back because it has been marked as rollback-only
	at org.springframework.transaction.support.AbstractPlatformTransactionManager.processCommit(AbstractPlatformTransactionManager.java:752) ~[spring-tx-5.3.22.jar:5.3.22]
	at org.springframework.transaction.support.AbstractPlatformTransactionManager.commit(AbstractPlatformTransactionManager.java:711) ~[spring-tx-5.3.22.jar:5.3.22]
	at org.springframework.transaction.interceptor.TransactionAspectSupport.commitTransactionAfterReturning(TransactionAspectSupport.java:654) ~[spring-tx-5.3.22.jar:5.3.22]
	at org.springframework.transaction.interceptor.TransactionAspectSupport.invokeWithinTransaction(TransactionAspectSupport.java:407) ~[spring-tx-5.3.22.jar:5.3.22]
	at org.springframework.transaction.interceptor.TransactionInterceptor.invoke(TransactionInterceptor.java:119) ~[spring-tx-5.3.22.jar:5.3.22]
	at org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:186) ~[spring-aop-5.3.22.jar:5.3.22]
	at org.springframework.aop.framework.CglibAopProxy$CglibMethodInvocation.proceed(CglibAopProxy.java:763) ~[spring-aop-5.3.22.jar:5.3.22]
	at org.springframework.aop.framework.CglibAopProxy$DynamicAdvisedInterceptor.intercept(CglibAopProxy.java:708) ~[spring-aop-5.3.22.jar:5.3.22]
	at org.abc.xyz.service.ParcelService$$EnhancerBySpringCGLIB$$b8eae53a.updateParcelFileInfo(<generated>) ~[classes/:na]
	at org.abc.xyz.service.fulfillment.schedule.ParcelFileAutoGenerator.execute(ParcelFileAutoGenerator.java:48) ~[classes/:na]
	at org.abc.xyz.job.AbstractJob.executeInternal(AbstractJob.java:19) ~[classes/:na]
	at org.springframework.scheduling.quartz.QuartzJobBean.execute(QuartzJobBean.java:75) ~[spring-context-support-5.3.22.jar:5.3.22]
	at org.quartz.core.JobRunShell.run(JobRunShell.java:202) ~[quartz-2.3.2.jar:na]
	at org.quartz.simpl.SimpleThreadPool$WorkerThread.run(SimpleThreadPool.java:573) ~[quartz-2.3.2.jar:na]
```

# Triggered by `SchedulerAccessor`
Within org/springframework/spring-context-support/5.3.22/spring-context-support-5.3.22-sources.jar!/org/springframework/scheduling/quartz/SchedulerAccessor.java

```java
		if (transactionStatus != null) {
			this.transactionManager.commit(transactionStatus);
		}
```

--HTH--