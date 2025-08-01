---
header:
    image: /assets/images/hd_bootstrap_logging_springboot.png
title: How logging system Bootstrapped in Spring Boot Application
date: 2021-12-21
tags:
 - SpringBoot
 - Java
 - Logback
 
permalink: /blogs/tech/en/boostrap_logging_in_springbootapplication
layout: single
---

# Summary
Following diagram demonstrated the process to bootstrap and use Logback for loggings in Spring Boot applciation.

# Video version of this explanation
If you'd perfer a more intuitive and vision version, check it out below.

<iframe width="560" height="315" src="https://www.youtube.com/embed/Q6GY8rLnyBc" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>



# Workflow diagram

![](/assets/images/BootstrapLoggingInSpringBoot.png)

# Key steps explained
> The first section for logic in SpringBoot Application domain

1. When a SpringBoot application start to execute SpringApplicaiton.run , internally it will execute `prepareEnvironment` , which will create or load application run environment , such as environment variables. 
2. SpringBoot use Observer Pattern and  SpringApplicationEvent to keep tack of each key steps in Spring Boot Application life cycle.  SpringBoot will pass loaded environments as argument to list of registered listeners. 

```java
listeners.environmentPrepared(bootstrapContext, environment);
```
3. SpringBoot's Event publisher (EventPublishingRunListener) will publish an event called **ApplicationEnvironmentPreparedEvent** via it's built-in multicast publisher.
4. **LoggingApplicationListener** is one of 6 components in Spring subscribed to ApplicationEnvironmentPreparedEvent. It will configure Spring's LoggingSystem. If the environment contains a logging.config property, it will be used to bootstrap the logging system, otherwise a default configuration is used.
5. SpringBoot will leverage Classloader to try to load any LoggingSystem or its descendants.
6. If you added sl4j into class path, LoggingSystemFactory will produce a new LogbackLoggingSystem, which extended LoggingSystem ultimately. 

```java
return new LogbackLoggingSystem(classLoader);
```
> Now we move to domain of logging system in slf4j & logback. 


7. LogbackLoggingSystem will invoke doConfig  of SpringBootJoranConfigurator to setup logging sub system. This Configurator is backbone of Joran framework.

> Joran: a mature, flexible and powerful configuration framework. On which logback's configuration logic is based. Details check it out at Joran Configuration framework

8. **Interpreter** will parse configuration details in logback.xml , internally logback would convert elements of aforesaid xml file as a list of Event , then Interpreter has one EventPlayer to process those events one by one.e
9. **Interpreter** is Joran's main driving class. It extends SAX DefaultHandler which invokes various actions according to predefined patterns (configured as RuleStore ). It leverage Constructor to start a new instance of LogstashEncoder in memory.
10. **Joran** defines StartEvent  and EndEvent  to process beginning and ending element in XML configuration. For </encoder> , Joran will use reflection to call property setter of ConsolerAppender, and inject aforesaid logstashEncoder as property encoder .
11. This is the last step of this setup. When there are logs to be wrote, the log Appender's internal encoder  (that's LogstashEncoder in this case) will be invoked to render output message.

--End--

