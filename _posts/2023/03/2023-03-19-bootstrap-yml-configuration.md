---
title: spring_cloud_master_piece_2
header:
image: /assets/images/yarn_npm_install.jpg
date: 2023-03-19
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/spring_cloud_master_piece_2
layout: single
category: tech
---


# what's usage of bootstrap yml
In a Spring Boot application, the bootstrap.yml (or bootstrap.properties) file is used for configuring the application's environment and setting up the context in which the application will run.

Specifically, the bootstrap.yml file is loaded very early in the application startup process, even before the application's application.yml (or application.properties) file is loaded. This allows you to configure properties that are required for setting up the application context, such as configuring the Spring Cloud Config server or setting up the encryption/decryption keys for encrypted properties.

Here are some examples of how you might use the bootstrap.yml file in a Spring Boot application:

Setting up the Spring Cloud Config server:
yaml
Copy code
spring:
  cloud:
    config:
      uri: http://localhost:8888
      username: myuser
      password: mypassword
Setting up the encryption/decryption keys for encrypted properties:
yaml
Copy code
encrypt:
  key-store:
    location: classpath:/keystore.jks
    password: mypassword
    alias: myalias
    secret: mysecret
Configuring the application to use a different profile for the Spring Cloud Config server:
yaml
Copy code
spring:
  profiles:
    active: dev
  cloud:
    config:
      profile: dev
Note that the bootstrap.yml file is not always necessary for all Spring Boot applications. It is typically used for applications that require more complex configuration setup or for applications that use Spring Cloud Config or other similar external configuration servers. For simpler applications, you may be able to get away with just using the application.yml file.


# Here are some best practices for using bootstrap.yml in a microservice environment:

Use bootstrap.yml for configuration that is required for setting up the application context. This could include configuration for things like service discovery, security, or external configuration servers.
Keep the bootstrap.yml file small and focused on setting up the application context. Avoid putting configuration that is specific to a particular microservice in the bootstrap.yml file, as this can make it harder to manage and maintain.
Use different bootstrap.yml files for different environments (e.g. development, testing, production). This can allow you to configure things like the Spring Cloud Config server or service discovery endpoints differently for each environment.
Use a configuration server like Spring Cloud Config to manage configuration for your microservices. This can help to centralize configuration management and ensure that all microservices have access to the same configuration properties.
Use encryption to secure sensitive configuration properties. Spring Cloud Config supports encryption and decryption of configuration properties, so you can store sensitive properties in the configuration server without exposing them to unauthorized access.
Be careful when using the spring.cloud.bootstrap.enabled property to disable bootstrap.yml processing. While this can be useful in some cases, it can also cause problems if the application relies on configuration that is normally set up in the bootstrap.yml file. If you need to disable bootstrap.yml processing, consider using a separate property file instead.

Use version control to manage changes to bootstrap.yml. Like any other code or configuration file, changes to bootstrap.yml should be tracked in version control to make it easier to revert changes or see when changes were made.
Use consistent naming conventions for configuration properties. This can help to make it easier to manage configuration across different microservices and can reduce the likelihood of typos or errors.
Document your configuration properties. Make sure that anyone who needs to work with the bootstrap.yml file understands what the different configuration properties do and how they should be configured.
Test your configuration. Make sure that your microservices are able to start up and run correctly with the configuration specified in bootstrap.yml. Use automated testing and integration testing to verify that your configuration is correct and that your microservices are able to communicate with each other and with external dependencies.
Overall, the best practices for using bootstrap.yml in a microservice environment are similar to the best practices for managing configuration in general: keep it focused, consistent, and well-documented, and use tools and processes to manage it in a centralized and secure way.

Avoid using bootstrap.yml to override default Spring Boot properties. Instead, use the application.yml file to override default Spring Boot properties. This can help to make your configuration more modular and easier to manage.
Consider using profiles to manage configuration for different environments. Spring Boot supports the use of profiles to manage configuration for different environments (e.g. development, testing, production). This can allow you to have different configuration for each environment while still keeping your code and configuration consistent.
Be aware of the order in which configuration files are loaded. When using multiple configuration files (e.g. bootstrap.yml and application.yml), be aware of the order in which they are loaded. By default, Spring Boot will load bootstrap.yml before application.yml, but you can change this order by using the spring.config.name and spring.config.location properties.
Use the spring.cloud.config.fail-fast property to control how the application behaves when it is unable to connect to the configuration server. By default, Spring Cloud Config will attempt to connect to the configuration server indefinitely, but you can use the spring.cloud.config.fail-fast property to control how many times it retries before giving up.



Use the spring.cloud.config.label property to specify the Git branch or tag to use for configuration. This can be useful if you need to manage different versions of configuration for different environments or releases.
Use the spring.cloud.config.profile property to specify the Spring profile to use for configuration. This can be useful if you need to manage different configuration properties for different environments or profiles.
Use the spring.cloud.config.discovery.enabled property to enable service discovery for the configuration server. This can allow your microservices to discover the configuration server automatically, which can make it easier to manage and maintain.
Consider using a Spring Cloud Config client library to simplify the process of accessing configuration properties from the configuration server. Spring Cloud Config provides a client library that can be used to access configuration properties in a more convenient and consistent way.
Monitor your microservices for configuration changes. Changes to configuration can have a big impact on the behavior and performance of your microservices, so it's important to monitor them for changes and to ensure that changes are communicated to the relevant stakeholders. Use tools like Spring Cloud Bus and Spring Cloud Stream to propagate configuration changes across your microservices and to alert you when configuration changes occur.
By following these best practices, you can ensure that your microservices are able to access the configuration properties they need to run correctly and that your configuration management process is efficient, secure, and reliable
