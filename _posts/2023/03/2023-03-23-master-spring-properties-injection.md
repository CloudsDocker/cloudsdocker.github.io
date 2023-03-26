---
title: A Brief Introduction To Lookbehind And Lookahead In Regular Expressions
header:
    image: /assets/images/why-regexp-look-ahead-look-behind.jpg
date: 2023-03-20
tags:
 - RegularExpression
 - Regexp
 - Python

permalink: /blogs/tech/en/why-regexp-look-ahead-look-behind
layout: single
category: tech
---
> "The only way to do great work is to love what you do." - Steve Jobs


In Spring Boot, the @ConfigurationProperties annotation is used to bind external configuration properties to a Java class. The prefix in @ConfigurationProperties is used to define a specific namespace for the properties that will be bound to the class.

The naming convention for the prefix follows kebab-case (lowercase words separated by hyphens), which is commonly used for property names in Spring Boot applications. For example:

java
Copy code
@ConfigurationProperties(prefix = "app.config")
public class AppConfigProperties {
    private String name;
    private int timeout;
    // getters and setters
}
In this example, the prefix "app.config" is defined, and properties with this prefix in the external configuration (such as application.properties or application.yml) will be bound to the corresponding fields in the AppConfigProperties class:

arduino
Copy code
app.config.name=my-application
app.config.timeout=3000
When creating a prefix, it is a good practice to follow these guidelines:

Use a meaningful name that represents the functionality or module related to the properties.
Keep it short and easy to remember.
Follow the kebab-case naming convention.
Avoid using reserved words or conflicting with other commonly used prefixes in your application.



todd zhang
More

Here's more information on using @ConfigurationProperties in Spring Boot applications:

Nested properties: You can use nested properties to group related configurations together. This is particularly useful for larger applications with complex configurations. To do this, create nested classes within the class annotated with @ConfigurationProperties. The nested properties follow the same kebab-case naming convention. For example:
java
Copy code
@ConfigurationProperties(prefix = "app.config")
public class AppConfigProperties {
    private String name;
    private int timeout;
    private Database database;

    // getters and setters

    public static class Database {
        private String url;
        private String username;
        private String password;
        // getters and setters
    }
}
In this case, the external configuration properties would look like:

arduino
Copy code
app.config.name=my-application
app.config.timeout=3000
app.config.database.url=jdbc:mysql://localhost:3306/mydb
app.config.database.username=user
app.config.database.password=secret
Validating properties: Spring Boot allows you to validate the configuration properties by using JSR-303 annotations like @NotNull, @Min, @Max, etc. To enable validation, add the @Validated annotation to the class with @ConfigurationProperties, and include the necessary validation annotations on the fields. For example:
java
Copy code
@ConfigurationProperties(prefix = "app.config")
@Validated
public class AppConfigProperties {
    @NotNull
    private String name;

    @Min(1000)
    @Max(10000)
    private int timeout;

    // getters and setters
}
Registering ConfigurationProperties classes: To make a @ConfigurationProperties class available for use, you need to either:
Annotate it with @Component and let component scanning pick it up. This is useful if you want to use the properties class in multiple places.
Declare a bean for the class in a configuration class using @EnableConfigurationProperties or @Bean. This is useful if you want to control the scope or lifecycle of the bean or use constructor injection to set its dependencies.
For example, using @EnableConfigurationProperties in a configuration class:

java
Copy code
@Configuration
@EnableConfigurationProperties(AppConfigProperties.class)
public class ApplicationConfiguration {
    // ...
}
By following these guidelines and practices, you can effectively manage and organize configuration properties in your Spring Boot applications.



