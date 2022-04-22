---
header:
    image: /assets/images/fat_jar_spring_boot.png
title:  One page to cover most commonly found errors for fat jar in SpringBoot
date: 2022-04-22
tags:
 - springboot
 - java
 - jar
 
permalink: /blogs/tech/en/fat_jar_errors_in_spring_boot
layout: single
category: tech
---

> Kill time, or kiss time!

# Summary

As you know, `fat jar` is the jar file can be executed via `java -jar abc.jar`, because all configuration and dependencies included by default.

However, there are few errors found working with fat jar. This is a page to summarize and show how to get the point to fix it directly. 

# Errors

## no main manifest attribute, in  xxx.jar

The error looks like below:
```
no main manifest attribute, in your-dummy-service-1.0-SNAPSHOT.jar
```
## Error: Could not find or load main class

```
Error: Could not find or load main class com.dummy.hr.WorkflowServiceRunner
Caused by: java.lang.NoClassDefFoundError: org/springframework/boot/CommandLineRunner
```

# troubleshooting 
Those errors indicate your `fat-jar` don't work propperly. You can try following steps for troubleshooting:

## Open generated jar file under folder `/targer`
Firstly run command to generate the file, e.g. `mvn clean install` 
then check your target folder within IDE. As below screenshot:
![](/assets/images/fat_jar_target.png)

(1) The fat-jar jar file will be saved to target folder.
(2) There should be two files one in `your-name.jar` and another is `your-name.jar.original`. 
(3) The difference is your-name.jar.original is the *original* file from your code, then *sprint-boot* hijacked it to injected several logis, such as setup SpringBootApplication annotated main-class , spring-boot guessed dependencies, etc. 
(4) Open the file MANIFEST.MF, this is the file contains metadata for this fat-jar
(5) The Main class should be updated to `org.springframework.boot.loader.JarLauncher` in step #3.
(6) Then the varaible `Start-Class: com.xxxservice.xxxServiceApplicationMain` is your main class annoted with `@SpringBootApplication`

# Solution
There are several possible reasonse to cause the fat jar failed to generate. While here are some note-worthy points for fix.

(1) To add parent element `spring-boot-starter-parent` in front of your applicationo defintiona in pom.xml
```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.5.3</version>
    <relativePath/> 
</parent>

<groupId>com.dummy</groupId>
<artifactId>abc-workflow-service</artifactId>
<version>1.0-SNAPSHOT</version>
```   
(2) To add `build/plugins` at bottom of pom.xml, be advised its NOT `build/pluginManagement/plugins`

```
<build>
    <plugins>
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
            <version>2.6.6</version>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <configuration>
                <source>11</source>
                <target>11</target>
            </configuration>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-resources-plugin</artifactId>
            <version>2.4</version>
        </plugin>
    </plugins>
</build>
```

--HTH--



