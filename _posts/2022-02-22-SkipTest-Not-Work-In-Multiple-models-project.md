---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  SkipTest-Not-Work-In-Multiple-models-project
date: 2022-02-02
tags:
 - Maven
 - Java
 - Errors
 
permalink: /blogs/tech/en/mvn_failed_to_skip_tests_in_multiple_modules_project
layout: single
category: tech
---

> Leave nothing for tomorrow which can be done today. -Abraham Lincoln.



# Background & symptoms

As you know, you can skip tests during maven run, which maybe because you want to get an urgent task down or test will result in some noisy.

You alreay know, you can run following command to skip test

```java
mvn install -DskipTests
```
# Failures!
However, this skipTest won't work for project with `multiple modules`, for example if you run above command in **parent** module, each child project will still trigger *test* phase. 

To solve the problem, please use following command alternatively. 

Specifically, it's **-Darguments=-DskipTests**

```bash
mvn -Darguments=-DskipTests install
```

--End--



