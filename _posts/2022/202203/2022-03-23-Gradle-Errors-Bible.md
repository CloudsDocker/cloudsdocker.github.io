---
header:
    image: /assets/images/hd_gradle_errors.png
title:  Bible blog for most commonly found Gradle errors
date: 2022-03-23
tags:
 - Gradle
 - Java
 - Programing
 
permalink: /blogs/tech/en/gradle_errors_solutions_bible
layout: single
category: tech
---

> People are smarter than you think. Give them a chance to prove themselves.

# Unknown host 'repo.maven.apache.org'. You may need to adjust the proxy settings in Gradle.
This error normally happen if your project is within company's firewall. 
For error when you firstly loaded a Gradle project, the message look like:

*Unknown host 'repo.maven.apache.org'. You may need to adjust the proxy settings in Gradle.*
Enable Gradle 'offline mode' and sync project
Learn about configuring HTTP proxies in Gradle

## solution
Create and add a file gradle.properties to your home directory. E.g. add following file gradle.properties
C:\Users\USER_NAME\.gradle\gradle.properties
Here are contents
```bash
systemProp.http.proxyHost=proxy.your.company.proxy.com
systemProp.http.proxyPort=8080
systemProp.http.proxyUser=your_user_name
systemProp.http.proxyPassword=password
systemProp.http.nonProxyHosts=*.nonproxyrepos.com|localhost
systemProp.https.proxyHost=proxy.your.company.proxy.com
systemProp.https.proxyPort=8080
systemProp.https.proxyUser=your_user_name
systemProp.https.proxyPassword=password
systemProp.https.nonProxyHosts=*.nonproxyrepos.com|localhost
```

# Could not find method compile() for arguments

There error is *Could not find method compile() for arguments [org.springframework.boot:spring-boot-starter] on object of type org.gradle.api.internal.artifacts.dsl.dependencies.DefaultDependencyHandler.*

* Try:
Run with --info or --debug option to get more log output. Run with --scan to get full insights.

## troubleshooting
Note that the compile, runtime, testCompile, and testRuntime configurations introduced by the Java plugin have been deprecated since Gradle 4.10 (Aug 27, 2018), and were finally removed in Gradle 7.0 (Apr 9, 2021).

## Solution
You either **downgrade** your Gradle runtime to older version prior to v7.0.
Or update `build.gradle` to 
 - Replace `compile` with `implementation`
 - Replace `runtime` with `runtimeOnly`
 - Replace `testCompile` with `testImplementation`
 - Replace `testRuntime` with `testRuntimeOnly`

 
--End--



