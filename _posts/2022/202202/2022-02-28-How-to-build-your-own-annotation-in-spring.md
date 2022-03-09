---
header:
    image: /assets/images/hd_jpa_springdata.png
title:  What's inside magic in Spring Data JPA
date: 2022-02-25
tags:
 - SpringBoot
 - Java
 - SpringData
 
permalink: /blogs/tech/en/build_own_spring_annotation
layout: single
category: tech
---

> A good day starts with a good mindset!



```java

@Target({ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER, ElementType.ANNOTATION_TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Value("${spring.application.name}")
public @interface GetAppName {
}


///


@GetAppName
private String appName;

 ```
--END--




