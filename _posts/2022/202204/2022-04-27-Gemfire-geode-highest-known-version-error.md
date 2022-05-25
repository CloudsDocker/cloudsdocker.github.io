---
header:
    image: /assets/images/hd_geode_ordinal.png
title:  Gemfire Geode Error on Peer or client version with ordinal xx not supported. Highest known version is 1.12.1 Client
date: 2022-04-27
tags:
 - springboot
 - java
 - Geode
 - Gemfire
 
permalink: /blogs/tech/en/Gemfire-geode-highest-known-version-error
layout: single
category: tech
---

> Take the risk or lose the chance!

# Summary
When you try to start a service using Gemfire/Geode, you may get following error:

```
WARN 30684 --- [Timer-DEFAULT-3] o.a.g.c.c.i.ConnectionFactoryImpl        : Could not create a new connection to server: 12.213.123.115(aa22233455_server:40393)<v1>:41001(version:GEODE 1.12.1)
refused connection: Peer or client version with ordinal 125 not supported. Highest known version is 1.12.1 Client: /10.18.103.161:64617.
```


# Troubleshoot
Dive into the error stack trace, this error is server  rejected handshake request from client, the reply is refused code **60**. As per checking Gemfire code, it defined as below
```
protected static final byte REPLY_REFUSED = (byte) 60;
```

![](/assets/images/Gemfire%20errors_ordinal.png)

# Ultimate solution

Firstly, remove all open source geode library with pivotal one
Remove all geode/gemfire dependencies if you'd want a clean start.

Then including geode-core from pivotal as below
```xml
<dependency>
     <groupId>io.pivotal.gemfire</groupId>
     <artifactId>geode-core</artifactId>
     <version>9.10.14</version>
</dependency>
```xml

Moreover, to include spring-data-geode  or spring-data-gemfire which provide `GemfireTemplate` classes. E.g. following dependencies into your pom.xml as well
```xml
<dependency>
        <groupId>org.springframework.data</groupId>
        <artifactId>spring-data-gemfire</artifactId>
        <version>2.3.5.RELEASE</version>
 </dependency>
```
> Bottom line is use spring-data-geode in version 2.3.X (rather than 2.5.x)
![](/assets/images/spring_data_geode_version.png)


One of the reason to lead to unexpected spring-data-geode 2.5.x is using higher version of Spring boot.  So  as below

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <!--        <version>2.5.3</version>-->
    <version>2.3.1.RELEASE</version>
    <relativePath/> 
</parent>
```

--HTH--



