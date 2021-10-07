---
title: Deep dive into ApplicationEvent in SpringBoot
date: 2021-10-07
tags:
 - SpringBoot
 - ApplicationEvent
layout: single
category: tech
---

# Summary
As you know,  there are various `event` will be sent (multicast) when a specific story taken place.

This simple blog will walk through the list of key `ApplicationEvent` when you kick start a Spring Boot applicaiton. So that you'll get an insight into how SpringBoot application bootstraped and started to serving requests.

# Key application events

## Holistic diagram view

![](/assets/images/SpringBootApplicationEvent.png)

## ApplicationStartingEvent

> Event published as early as conceivably possible as soon as a SpringApplication has been started - before the Environment or ApplicationContext is available, but after the ApplicationListeners have been registered. 

This is called in SpringApplication.java 's run method.

```java
listeners.starting(bootstrapContext, this.mainApplicationClass);
```

## ApplicationEnvironmentPreparedEvent
> Event published when a SpringApplication is starting up and the Environment is first available for inspection and modification.

This is triggered in SpringApplication's prepareEnvrionment method, which indica envrionment configured.

## ApplicationContextInitializedEvent
> Event published when a SpringApplication is starting up and the ApplicationContext is prepared and ApplicationContextInitializers have been called but before any bean definitions are loaded.

This is triggered in SpringApplication's prepareContext method, which indicate context initialized and context inititializers are called.

## ApplicationPreparedEvent

> Event published as when a SpringApplication is starting up and the ApplicationContext is fully prepared but not refreshed. The bean definitions will be loaded and the Environment is ready for use at this event.

This is called at last step of SpringApplication's prepareContext method, which indicate ApplicationContext is loaded

## ObjectMapperConfigured (optional)
> This is used for MvcObjectMapper

This is come from WebMvcObjectMapperConfigurer, it's actually means HttpMessageConverter beans configured. Those used in Mvc's RequestMappingHandlerAdapter

## ServletWebServerInitializedEvent (optional)
> Event to be published after the WebServer is ready. Useful for obtaining the local port of a running server.
Normally it will have been started, but listeners are free to inspect the server and stop and start it if they want to.

This is triggered in WebServerStartStopLifecycle.java#start() method, after calling underlying webserver's start method and set "running" flag to true.

Because WebServerStartStopLifecycle implemented SmartLifecycle, and it's autoStartup flag is true, so AbastractApplicationContext's finsihRefresh will call all lifecycleProcessoer.onRefresh(), which will invoke lifeCycle's start() method.

Ultimately this is called when SpringApplicatin to refresh(context)

## ContextRefreshedEvent
> Event raised when an ApplicationContext gets initialized or refreshed.
This is thrown in AbstractApplicationContext#fresh()

```java
publishEvent(new ContextRefreshedEvent(this));
```



## ApplicationStartedEvent
> Event published once the application context has been refreshed but before any application and command line runners have been called.

It then will call following one to further publish availability change event

```java
AvailabilityChangeEvent.publish(context, LivenessState.CORRECT);
```


## AvailabilityChangeEvent
It's payload is "CORRECT"

public enum LivenessState implements AvailabilityState {
"Liveness" state of the application.
An application is considered live when it's running with a correct internal state. "Liveness" failure means that the internal state of the application is broken and we cannot recover from it. As a result, the platform should restart the application.


After this event, SpringApplication's "run" method will be invoked, normally you'll call start method of your service/runner


## ApplicationReadyEvent
> Event published as late as conceivably possible to indicate that the application is ready to service requests. 

Then it will invoke another event for Accepting_traffic

##  AvailabilityChangeEvent

ApplicationEvent sent when the AvailabilityState of the application changes.

When starting Spring Application, this state will be "ACCEPTING_TRAFFIC"

"Tada!" when you get this event, it means your SpringApplication started and happy to accept requests from users.

--End--
