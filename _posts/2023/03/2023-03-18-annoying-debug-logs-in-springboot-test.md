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
 
    

--HTH--
