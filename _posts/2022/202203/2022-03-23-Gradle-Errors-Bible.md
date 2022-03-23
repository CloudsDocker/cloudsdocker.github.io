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

> People are smarter than you think. Give them a chance to rpove themeselves.

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

--End--



