---
header:
    image: /assets/images/hd_jpa_springdata.png
title:  How to build your own annotation in spring
date: 2022-02-28
tags:
 - SpringBoot
 - Java
 - Annotation
 
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




