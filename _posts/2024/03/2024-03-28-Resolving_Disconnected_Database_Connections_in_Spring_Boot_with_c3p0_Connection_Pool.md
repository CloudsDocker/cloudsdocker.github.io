---
title: Resolving Disconnected Database Connections in Spring Boot with c3p0 Connection Pool
header:
    image: /assets/images/2024/2024_03_28.jpg
date: 2024-03-28
tags:
- Java
- Programming
- IntelliJ

permalink: /blogs/tech/en/Resolving_Disconnected_Database_Connections_in_Spring_Boot_with_c3p0_Connection_Pool
layout: single
category: tech
---
> “Everything is easy, once you know the answer.  —Dave Magee

# Introduction:

In a recent production issue, we encountered the error 

`org.springframework.dao.DataAccessResourceFailureException: could not extract ResultSet; nested exception is org.hibernate.exception.JDBCConnectionException: 
`

and

`could not extract ResultSet The client was disconnected by the server because of inactivity. See wait_timeout and interactive_timeout for configuring this behavior.
`

This error indicates that the MySQL database server was terminating idle connections due to inactivity exceeding a specific timeout threshold.

# Understanding the Problem:

This issue arises from a combination of factors:

 - **c3p0 Connection Pool and MaxIdleTime**: 
   - Your Spring Boot application utilizes the c3p0 connection pool. By default, if _`maxIdleTime`_ in your `application.yaml` file is not explicitly set, it defaults to 0, meaning connections never become idle.
 - **MySQL Server Timeout:** 
   - The MySQL database server has its own configuration for connection timeouts, such as interactive_timeout, which can be retrieved using the command 
   `SHOW GLOBAL VARIABLES LIKE 'interactive_timeout'`.   
   - In this case, this timeout was set to _3600_ seconds (1 hour).

## The Root Cause:

The interplay between these factors creates the problem:

 - Connections are opened in the c3p0 pool but remain idle indefinitely due to the default `maxIdleTime` of 0.
 - When these idle connections exceed the MySQL server's `interactive_timeout` of 1 hour, the server terminates them.
 - The Java application attempts to use an already terminated connection, resulting in the `DataAccessResourceFailureException`.

## Resolving the Issue:

Here's a straightforward solution to prevent this issue:

 - **Set a Reasonable maxIdleTime**: In your `application.yaml` file, explicitly configure the `maxIdleTime` property for the c3p0 connection pool. A common value is 30 seconds, allowing connections to become idle and potentially be reused within that timeframe before being closed by the pool.

 
 
Example application.yaml:

```yaml
spring:
  datasource:
    hikari:  # Assuming you're using HikariCP (adjust if using c3p0 directly)
      maxIdle: 30  # Set maxIdleTime to 30 seconds

```


# Explanation:

By setting `maxIdleTime` to 30 seconds, connections that remain idle for more than 30 seconds are returned to the c3p0 pool and potentially reused by the application. This prevents them from reaching the MySQL server's 1-hour timeout and being terminated.

# Conclusion:

This solution effectively addresses the `DataAccessResourceFailureException` by ensuring that idle connections are managed appropriately within the application's c3p0 pool, preventing them from exceeding the MySQL server's timeout. This improves application stability and resource utilization.

By implementing this fix, you'll ensure that your Spring Boot application maintains a healthy connection pool and avoids unexpected database connection disruptions.

# Sources

 - https://tridion.stackexchange.com/questions/19206/publishing-status-stuck-on-waiting-for-deployment-sdl-web-8-5
 - https://dev.mysql.com/doc/relnotes/connector-cpp/en/news-8-0-24.html

--HTH--