---
title: Why Hibernate Still Logs SQL Even When Disabled in application.yaml
header:
    image: /assets/images/2024/04/04/header.jpg
date: 2024-05-01
tags:
- Java
- Programming
- Spring Boot
- Hibernate

permalink: /blogs/tech/en/Why_Hibernate_Still_Logs_SQL_Even_When_Disabled_in_application.yaml
layout: single
category: tech
---
> Good leadership consists of doing less and being more.  —Dave Ramsey

This blog post explores a troubleshooting scenario where Hibernate continued to output SQL statements in logs even after disabling it in the application.yaml file. It serves as a guide for your team to understand property setting logic in Spring Boot and Hibernate.

# The Problem
The issue arose when SQL queries persisted in the logs despite setting `hibernate.show_sql` to `false` in `application.yaml`.

# Investigation
## Code Review: The investigation delved into the source code of Hibernate (`hibernate-core-5.6.10.Final`), specifically:

- `SqlStatementLogger.java`: This class defines the `logStatement` method responsible for logging SQL statements.
- `JdbcServicesImpl.java`: This class configures the `SqlStatementLogger` based on properties like showSQL.  - ![img.png](/assets/images/2024/05/01/image.png)
- `StandardServiceRegistryImpl.java`: This class accepts a `configurationValues` map containing Hibernate properties.
## Property Setting Flow: The code revealed the following flow for setting Hibernate properties:

 - `StandardServiceRegistryBuilder` is created with `configurationValues`.
 - This builder applies the settings to the internal registry.
 - `EntityManagerFactoryBuilderImpl` uses this registry during building.
 - Ultimately, the properties are set from 1 in your project.
# The Culprit
The investigation identified `MasterJpaConfiguration.java` as the source of the issue. It explicitly set `hibernate.show_sql` to `true`, overriding any potential `false` setting from `application.yaml`.

# Fixing the Issue
To resolve the problem, you can:

- Remove the `hibernate.show_sql` property from `MasterJpaConfiguration.java`.
- Set `hibernate.show_sql` to `false` in` application.yaml` if intended for global configuration.
# Tips for Future Troubleshooting
When encountering unexpected behavior related to Hibernate properties:

 - Search your project for keywords like `hibernate.show_sql` or use wildcards like `hibernate.show_sql*`.
 - ![img.png](/assets/images/2024/05/01/image-2.png)
 - Remember that properties set in Java code (like `MasterJpaConfiguration.java`) might override those from configuration files (like `application.yaml`).
This blog post demonstrates a structured approach to troubleshooting Hibernate property settings in Spring Boot applications. 
By understanding the property flow and using proper search techniques, your team can effectively resolve similar issues in the future.


--HTH--