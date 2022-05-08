---
header:
    image: /assets/images/hd_json_mapping_error.png
title:  Could not write JSON: Value out of range. Value: "xxxxx" Radix:10
date: 2022-05-08
tags:
 - Jackson
 - Json
 - Gson
 - SpringBoot
 - SpringMVN
 
permalink: /blogs/tech/en/could_not_write_json_radix_10_error_in_spring_mvc
layout: single
category: tech
---

> Life is really simple, but men insist on making it complicated.

# Summary
In some case, to return objects for a RESTful call declared in `Controller`, via Spring or SpringBoot. You may face an exception like below

*HttpMessageNotWritableException: Could not write JSON: Value out of range. Value:"20220406" Radix:10;* 


# Error details

Here is one full error log for such case
```
.w.s.m.s.DefaultHandlerExceptionResolver : Resolved [org.springframework.http.converter.HttpMessageNotWritableException: Could not write JSON: Value out of range. Value:"20220406" Radix:10; nested exception is com.fasterxml.jackson.databind.JsonMappingException: Value out of range. Value:"20220406" Radix:10 (through reference chain: org.springframework.statemachine.support.DefaultExtendedState["variables"]->org.springframework.statemachine.support.ObservableMap["my-workflow-step1-datetime"]→com.google.gson.JsonPrimitive["asByte"])]
```

# Troubleshoot & explanation
As you know, when you define one output for a RESTful mapping method (e.g. `GetMapping`). Internally, Spring will invoke a mechanism called `HttpMessageConverter` to transform message.

In Spring-web, there is one class for this case is *AbstractGenericHttpMessageConverter.java*

Afterwards, corresponding concreate Serializer will determined based on data type. E.g. if method return type is a `Map`, one MapSerializer.java from jackson-databind will be employed. As per below screenshot

![](/assets/images/jackson_errors_radix_1.png)

The root cause of this error is Jackson will guess and try to convert value to a String. For this test case, it will try to convert it to `byte` which will failed at last.

As below highlighted errors:
![](/assets/images/jackson_errors_radix_2.png)

# solution
Due to the message is in Gson.JsonPrimitive, we can let Spring to use Google Gson library as default Json converter library, to replace JackSon Json as Spring's default Json converter.

To config it, update your application.yml or application.properties.

```yaml
spring:
  mvc:
    converters:
      preferred-json-mapper: gson
```






--HTH--



