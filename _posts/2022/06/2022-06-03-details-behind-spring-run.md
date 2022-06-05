---
header:
    image: /assets/images/hd_spring_boot_run_magic.png
title:  Magic after maven target spring-boot-run
date: 2022-06-03
tags:
 - SpringFramework
 - Java
 - Spring
permalink: /blogs/tech/en/spring-boot-run-behind-the-scene
layout: single
category: tech
---

# Summary
It's obviously almost everyone of us started to use *spring-boot* few years ago. To kick start a SpringBootApplication, you can either start it from run button in IDE or using following maven command

```
mvn spring-boot:run
```

Then you may wonderings what's the magic to use this command to kick start a Spring Boot application?

# Details explained

The Spring Boot Maven plugin includes a run goal which can be used to quickly compile and run your application. Applications run in an exploded form just like in your IDE.

If you navigate to **RunMojo.java** in project `spring-boot-maven-plugin` ，you'll find its the code logic to `mvn spring-boot:run`. That's the instruction to Java program. 

There are two key methods,
(1) `runWithForkedJvm`
(2) `runWithMavenJvm`

If you keep pom.xml as default, it will actually run `runWithForkedJvm`，however, if you config pom.xml as below, it will actually kick start `runWithMavenJvm`

```xml
<plugin>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-maven-plugin</artifactId>
    <configuration>
        <mainClass>${start-class}</mainClass>
        <classifier>deployable</classifier>
    </configuration>
    <executions>
        <execution>
            <id>default-cli</id>
            <goals>
                <goal>run</goal>
            </goals>
            <phase>none</phase>
            <configuration>
                <fork>true</fork>
                <jvmArguments>${jvm.args} -Ddns.server=127.0.0.1 -Dspring.profiles.active=local</jvmArguments>
                <folders>
                    <folder>${basedir}/src/test/resources</folder>
                </folders>
            </configuration>
        </execution>
    </executions>
</plugin>
```

BTW, if you willing to debug maven plugin, replace `mvn`  with `mvnDebug`, then check following lines:

[INFO] Attaching agents: []
Listening for transport dt_socket at address: 5050

You can create a remote debug attach to it for troubleshooting. 

-HTH-
