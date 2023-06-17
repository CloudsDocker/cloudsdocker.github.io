---
title: Deep dive for errors during Spring Boot Tests
header:
    image: /assets/images/GoogleMap_missing_JPN.jpg
date: 2023-03-28
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/errors-deep-dive-in-spring-boot-tests
layout: single
category: tech
---
# Transaction silently rolled back because it has been marked as rollback-only

```shell
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

## Triggered by `SchedulerAccessor`
Within org/springframework/spring-context-support/5.3.22/spring-context-support-5.3.22-sources.jar!/org/springframework/scheduling/quartz/SchedulerAccessor.java

```shell
if (transactionStatus != null) {
    this.transactionManager.commit(transactionStatus);
}
```
## Troubleshooting and solution
This is mainly because some of other methods populates exceptions, and Spring @transaction annotation mark current transaction as rollback which will mark current transaction

So please look into the console logs for details, and if possible, to change the log level from INFO to DEBUG. 

Additionally, you can also add `@Transactional(propagation = Propagation.REQUIRES_NEW)` to the method which you want to run in a new transaction.


# Unable to detect database type

Errors as below:
```shell
Caused by: java.lang.IllegalStateException: Unable to detect database type
	at org.springframework.util.Assert.state(Assert.java:76)
	at org.springframework.boot.jdbc.init.PlatformPlaceholderDatabaseDriverResolver.determinePlatform(PlatformPlaceholderDatabaseDriverResolver.java:132)
	at org.springframework.boot.jdbc.init.PlatformPlaceholderDatabaseDriverResolver.lambda$resolveAll$0(PlatformPlaceholderDatabaseDriverResolver.java:96)
	at org.springframework.boot.jdbc.init.PlatformPlaceholderDatabaseDriverResolver.resolveAll(PlatformPlaceholderDatabaseDriverResolver.java:121)
	at org.springframework.boot.jdbc.init.PlatformPlaceholderDatabaseDriverResolver.resolveAll(PlatformPlaceholderDatabaseDriverResolver.java:96)
	at org.springframework.boot.autoconfigure.quartz.QuartzDataSourceScriptDatabaseInitializer.resolveSchemaLocations(QuartzDataSourceScriptDatabaseInitializer.java:105)
	at org.springframework.boot.autoconfigure.quartz.QuartzDataSourceScriptDatabaseInitializer.getSettings(QuartzDataSourceScriptDatabaseInitializer.java:89)
	at org.springframework.boot.autoconfigure.quartz.QuartzDataSourceScriptDatabaseInitializer.<init>(QuartzDataSourceScriptDatabaseInitializer.java:51)
	at org.springframework.boot.autoconfigure.quartz.QuartzAutoConfiguration$JdbcStoreTypeConfiguration.quartzDataSourceScriptDatabaseInitializer(QuartzAutoConfiguration.java:143)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:566)
	at org.springframework.beans.factory.support.SimpleInstantiationStrategy.instantiate(SimpleInstantiationStrategy.java:154)
	... 92 more
```
## Troubleshooting and solutions
This error message is actually a bit misleading, it is not because of the database type, but because of the database connection related under the hood.
So in order to fix this, you need to make sure the database connection is correct. And eliminate this misleading error message first. 
You can add below code to your test class to mock this and skip *real* error so that eliminate this error message:

```kotlin
@MockBean
private lateinit var quartzDataSourceScriptDatabaseInitializer: QuartzDataSourceScriptDatabaseInitializer
```
Once you have eliminated this error message, you can start to troubleshoot the real error message. For example, below is the real error message:

```shell
java.sql.SQLSyntaxErrorException: Unknown database 'your_db_20230326'
	at com.mysql.cj.jdbc.exceptions.SQLError.createSQLException(SQLError.java:120)
	at com.mysql.cj.jdbc.exceptions.SQLExceptionsMapping.translateException(SQLExceptionsMapping.java:122)
	at com.mysql.cj.jdbc.ConnectionImpl.createNewIO(ConnectionImpl.java:828)
	at com.mysql.cj.jdbc.ConnectionImpl.<init>(ConnectionImpl.java:448)
	at com.mysql.cj.jdbc.ConnectionImpl.getInstance(ConnectionImpl.java:241)
	at com.mysql.cj.jdbc.NonRegisteringDriver.connect(NonRegisteringDriver.java:198)
	at com.mchange.v2.c3p0.DriverManagerDataSource.getConnection(DriverManagerDataSource.java:175)
	at com.mchange.v2.c3p0.WrapperConnectionPoolDataSource.getPooledConnection(WrapperConnectionPoolDataSource.java:220)
	at com.mchange.v2.c3p0.WrapperConnectionPoolDataSource.getPooledConnection(WrapperConnectionPoolDataSource.java:206)
	at com.mchange.v2.c3p0.impl.C3P0PooledConnectionPool$1PooledConnectionResourcePoolManager.acquireResource(C3P0PooledConnectionPool.java:203)
	at com.mchange.v2.resourcepool.BasicResourcePool.doAcquire(BasicResourcePool.java:1176)
	at com.mchange.v2.resourcepool.BasicResourcePool.doAcquireAndDecrementPendingAcquiresWithinLockOnSuccess(BasicResourcePool.java:1163)
	at com.mchange.v2.resourcepool.BasicResourcePool.access$700(BasicResourcePool.java:44)
	at com.mchange.v2.resourcepool.BasicResourcePool$ScatteredAcquireTask.run(BasicResourcePool.java:1908)
	at com.mchange.v2.async.ThreadPoolAsynchronousRunner$PoolThread.run(ThreadPoolAsynchronousRunner.java:696)
```

--HTH--