---
header:
    image: /assets/images/hd_FirstCliff.jpg
title: Debug of SpringBoot run not working in IntelliJ
date: 2021-11-15
tags:
 - IntelliJ
 - Java
 - IntelliJ
permalink: /blogs/tech/en/debug_not_hit_intelliJ
layout: posts
---

# Normal approach to debug maven

Normaly if you want to debug a Java application, you can use following procedures
- Running application with mvnDebug, such as `mvnDebug spring-boot:run`
- This will open a port such as `5005`
- Then open IntelliJ, create a `remote JVM debug` , attach it to port 5005 for debug

![](/assets/images/Run_Debug_Configurations.png)

However, sometimes you'll find **your breakpoints nevet got hit**. 

# Better/Alternative way to solve this issue.

1. Open a new terminal **within Intellij** (rather than external command line window).

2. Navigate to your *project folder* where pom.xml saved

3. Run following command
```bash
mvn spring-boot:run  -D"spring-boot.run.jvmArguments"="-Dimport.dataset.list=importpb -Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=5005"
```
After a while, you'll see following message indicate progress is listenring at designed port

```bash
[INFO] Attaching agents: []
Listening for transport dt_socket at address: 5005
```

4. Then start a new JVM debug window on port 5005, as below screenshot:

![](/assets/images/Run_Debug_Configurations.png)

5. Start debug with aforesaid debug configuration
![](/assets/images/debugIconIntelliJ.png)

6. Then you'll see breakpoint you set will be hit. As per below screenshot
![](/assets/images/BreakpointSpringBootApplication.png)


--End--
