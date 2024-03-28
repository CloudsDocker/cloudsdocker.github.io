---
title: 使用 c3p0 连接池解决 Spring Boot 中断的数据库连接问题（解决 Spring Boot 中断的数据库连接问题）
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
> 一旦你知道答案，一切都会变得简单。” —— 戴夫·梅吉（Dave Magee）

# 简介（简介）:

在最近的一次生产问题中，我们遇到了以下错误：

`org.springframework.dao.DataAccessResourceFailureException: could not extract ResultSet; nested exception is org.hibernate.exception.JDBCConnectionException: 
`

and

`could not extract ResultSet The client was disconnected by the server because of inactivity. See wait_timeout and interactive_timeout for configuring this behavior.
`

该错误表明 MySQL 数据库服务器由于空闲连接的非活动时间超过特定超时阈值而终止了空闲连接。


# 先理解这个问题:

这个问题源于以下几个因素的共同作用：

 - **c3p0 连接池和 MaxIdleTime**:
   - 您的 Spring Boot 应用使用的是 c3p0 连接池。默认情况下，如果您没有在 `application.yaml` 文件中明确设置 `maxIdleTime`，它将默认为 0，这意味着连接永远不会变为闲置状态。 
 - **MySQL 服务器超时:** 
   - MySQL 数据库服务器有自己的一套连接超时配置，例如 `interactive_timeout`，您可以使用命令 `SHOW GLOBAL VARIABLES LIKE 'interactive_timeout'` 检索该值。 
   - 在此例中，此超时时间设置为 3600 秒（1 小时）。

## 根本原因:

这些因素之间的相互作用导致了问题：

 - 由于默认的 `maxIdleTime` 为 0，连接在 c3p0 池中打开，但会一直处于闲置状态。
 - 当这些闲置连接超过 MySQL 服务器的 1 小时 `interactive_timeout` 时，服务器会终止它们。
 - Java 应用尝试使用一个已经终止的连接，从而导致 `DataAccessResourceFailureException`。

## 解决问题:

以下是如何防止此问题的简单解决方案

 - **设置合理的 MaxIdleTime**：在您的 `application.yaml `文件中，明确配置 c3p0 连接池的 `maxIdleTime` 属性。一个常用的值是 30 秒，它允许连接变为闲置状态，并在该时间范围内被重新使用，然后再被连接池关闭。



示例 application.yaml：

```yaml
spring:
  datasource:
    hikari:  # Assuming you're using HikariCP (adjust if using c3p0 directly)
      maxIdle: 30  # Set maxIdleTime to 30 seconds

```


# 解释:

通过将 `maxIdleTime` 设置为 30 秒，闲置超过 30 秒的连接将被返回到 c3p0 连接池，并可能被应用程序重新使用。这可以防止它们达到 MySQL 服务器的 1 小时超时并被终止。

# 结论:

此解决方案通过确保应用程序的 c3p0 连接池中适当地管理闲置连接，从而有效地解决了 `DataAccessResourceFailureException` 问题，防止它们超过 MySQL 服务器的超时时间。这可以提高应用程序的稳定性和资源利用率。

通过实施此修复程序，您可以确保您的 Spring Boot 应用维护一个健康的连接池，并避免意外的数据库连接中断。

# 参考来源

 - https://tridion.stackexchange.com/questions/19206/publishing-status-stuck-on-waiting-for-deployment-sdl-web-8-5
 - https://dev.mysql.com/doc/relnotes/connector-cpp/en/news-8-0-24.html

--HTH--