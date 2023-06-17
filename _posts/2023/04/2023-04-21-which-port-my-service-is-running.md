---
title: which-port-my-service-is-running
header:
image: /assets/images/which-port-my-service-is-running.jpg
date: 2023-04-21
tags:
- ssh
- devops
- automation

permalink: /blogs/tech/en/how-to-install-sonarqube-via-docker
layout: single
category: tech
---

# Summary
As a Java developer, it's important to know how to find out which port number your Spring service is running on. This information is useful when you need to connect to the service from another application or when troubleshooting connection issues. In this blog, we'll discuss different ways to determine the port number of your Java Spring service.

## Method 1: Check the Console Log

When you start your Java Spring service, it will output some information to the console log. This log contains useful information, including the port number that the service is running on. Look for a line in the console log that contains the phrase "Tomcat started on port(s):" followed by the port number.

For example, if your service is running on port 8080, the console log will contain a line that looks like this:

```bash
Tomcat started on port(s): 8080 (http) with context path ''
```
This line tells you that your Java Spring service is running on port 8080 and that it can be accessed via HTTP.

> if you don't see aboe line, you can search belo wline

```bash
o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat initialized with port(s): 1794 (http)
```


## Method 2: Check the Application Properties

Another way to find out the port number of your Java Spring service is to check the application.properties file. This file contains configuration properties for your Spring application, including the server port number.

Open the application.properties file and look for a line that contains the property "server.port". The value of this property specifies the port number that your Spring service is running on.

For example, if your service is running on port 8080, the application.properties file will contain a line that looks like this:

```properties
server.port=8080
```

## Method 3: Check the Command-Line Arguments

When you start your Java Spring service, you can specify the port number as a command-line argument. This is useful when you want to start the service on a specific port number.

To check the port number specified in the command-line arguments, look for a line in the console log that contains the phrase "Tomcat started on port(s):" followed by the port number.

For example, if you started your service with the command "java -jar myapp.jar --server.port=8080", the console log will contain a line that looks like this:


```properties
Tomcat started on port(s): 8080 (http) with context path ''
```

# Conclusion

In this blog, we've discussed three different methods for finding out which port number your Java Spring service is running on. You can check the console log, the application.properties file, or the command-line arguments to determine the port number. Knowing the port number of your Spring service is important for connecting to it from other applications or troubleshooting connection issues.
