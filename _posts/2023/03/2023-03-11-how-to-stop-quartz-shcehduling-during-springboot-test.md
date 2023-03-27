---
title: how-to-stop-quartz-scheduling-during-springboot-test
header:
    image: /assets/images/GoogleMap_missing_JPN.jpg
date: 2023-03-18
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/how-to-stop-quartz-scheduling-during-springboot-test
layout: single
category: tech
---

# how-to-stop-quartz-scheduling-during-springboot-test

To stop Quartz from starting during a @SpringBootTest in Spring Boot, you can use the @MockBean annotation to replace the SchedulerFactoryBean with a mock object. This will prevent the actual scheduler from being created and started during the test.

Here's an example of how you can use this annotation to stop Quartz from starting during a test:


```java
import org.junit.jupiter.api.Test;
import org.quartz.Scheduler;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;

@SpringBootTest
public class MyTest {

    @Autowired
    private MyService myService;
    
    @MockBean
    private Scheduler scheduler;
    
    @Test
    public void testWithoutQuartz() {
        // your test code here
    }
}
```

In this example, we use the @MockBean annotation to replace the SchedulerFactoryBean with a mock object. This will prevent the actual scheduler from being created and started during the test.

Note that if you have other configurations that depend on Quartz, disabling Quartz may affect the behavior of your tests. Be sure to test your application thoroughly after disabling Quartz in your tests.

--HTH--
