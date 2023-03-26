---
title: Feature Flag Spring Boot
header:
    image: /assets/images/feature-flag-spring-boot.jpg
date: 2023-03-19
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/feature-flag-spring-boot
layout: single
category: tech
---

# summary Feature flag library in spring boot

In Spring Boot applications, you can use feature flags to enable or disable certain features of your application during runtime. This helps with testing, gradual rollouts, and quickly disabling problematic features without requiring a full deployment.

There are several feature flag libraries available that can be integrated with Spring Boot applications. Some popular ones include:

 - Unleash: Unleash is a widely-used feature toggle system that supports Spring Boot. It provides an Unleash server, an admin UI to manage feature flags, and a client SDK to integrate with your application. The official Java Unleash client can be found at https://github.com/Unleash/unleash-client-java.
 - Togglz: Togglz is another feature toggle library for Java applications. It offers a flexible and extensible framework for managing feature flags, and it integrates well with Spring Boot. The official website with more information and documentation is https://www.togglz.org/.
 - FF4J: FF4J, short for Feature Flipping for Java, is a powerful feature flag management library that provides a web console, REST API, and Spring Boot integration. It allows you to manage feature flags, properties, and even authorization rules. You can learn more about FF4J at https://ff4j.org/.
 - LaunchDarkly: LaunchDarkly is a feature management platform that offers a feature flag service for various languages and frameworks, including Spring Boot. It provides a comprehensive dashboard for managing feature flags, real-time updates, and advanced targeting capabilities. The official Java SDK can be found at https://docs.launchdarkly.com/sdk/server-side/java.
To integrate one of these libraries into your Spring Boot application, you will need to add the corresponding dependencies to your project, configure the library, and follow the specific library's documentation to set up and manage your feature flags. Each library has its own way of defining, managing, and evaluating feature flags, so it's essential to familiarize yourself with their respective documentation.

# real world sample for feature flag 
To help you further understand the potential of feature flags and how they can be applied in different scenarios, here are some real-world examples of how organizations use feature flags:

 - Facebook: Facebook uses feature flags extensively to test new features and improvements with a subset of their user base. This allows them to gather user feedback and measure the impact of changes before rolling them out to their entire user base. They also use feature flags to enable or disable specific features for different regions or user segments.
 - Netflix: Netflix uses feature flags to perform canary releases and A/B testing, enabling them to test new features and algorithms on a small subset of users before rolling them out more broadly. This approach allows them to make data-driven decisions and minimize the impact of potential issues.
 - Etsy: Etsy, an e-commerce platform, uses feature flags to manage feature rollouts and control the release of new features. This enables them to gradually roll out changes and monitor their impact on user experience and system performance.
 - Google: Google uses feature flags to test new features and improvements in their products, such as Google Maps and Gmail. They also use feature flags to manage the release of new features, gradually rolling them out to their user base and monitoring their impact.
By examining these real-world examples, you can see that feature flags are a valuable tool for managing the development and deployment of software applications. They enable organizations to test and iterate on new features, reduce risk, and make data-driven decisions about feature rollouts.

When implementing feature flags in your Spring Boot application, keep the following key principles in mind:

 - Use feature flags for specific, well-defined purposes.
 - Follow best practices for creating, managing, and removing feature flags.
 - Plan for the eventual removal of feature flags from your codebase.
 - Test your application with different feature flag configurations to ensure correct behavior.
 - By adhering to these principles and learning from real-world examples, you can effectively leverage feature flags in your Spring Boot application to manage feature rollouts, perform A/B testing, and more, while minimizing the potential risks and complexity associated with their use.


# Suggestions of best for starters

For beginners or those new to feature flag management, Unleash is a great choice to start with. It has a simple setup process and a clean, easy-to-use interface for managing feature flags. Unleash also provides good documentation and examples, which can be helpful for those who are just starting out.

Here are the basic steps to integrate Unleash with a Spring Boot application:

Add the Unleash dependency to your pom.xml (Maven) or build.gradle (Gradle) file.
Maven:

```xml
<dependency>
    <groupId>com.github.unleash</groupId>
    <artifactId>unleash-client-java</artifactId>
    <version>4.2.0</version>
</dependency>
```

## Configure Unleash in your application.properties or application.yml file:


```
unleash.api.url=http://localhost:4242/api
unleash.app.name=my-spring-boot-app
```

Create a bean for the Unleash instance in one of your configuration classes:

```java
@Configuration
public class UnleashConfig {

    @Bean
    public Unleash unleash() {
        UnleashConfig config = UnleashConfig.builder()
                .appName("my-spring-boot-app")
                .instanceId(UUID.randomUUID().toString())
                .unleashAPI("http://localhost:4242/api")
                .build();

        return new DefaultUnleash(config);
    }
}
```

Use the Unleash instance in your application code to check if a feature flag is enabled:

```
@Autowired
private Unleash unleash;

public void someMethod() {
    if (unleash.isEnabled("my-feature-flag")) {
        // Feature flag is enabled, perform the new feature's behavior
    } else {
        // Feature flag is disabled, perform the old behavior
    }
}
```

After setting up Unleash, you can start creating and managing your feature flags using the Unleash server and its user interface. For more information, refer to the Unleash documentation: https://docs.getunleash.io/.

Keep in mind that the best choice ultimately depends on your specific requirements and preferences. It's worth exploring different libraries to find the one that best suits your needs.


## How to add new unleash feature flag in spring boot application

To add a new feature flag (called a "toggle") in Unleash, you'll first need to set up the Unleash server and UI if you haven't already. The server is responsible for managing feature flags and serving them to your client applications.

To set up the Unleash server, you can use the official Docker image. Follow these steps:

Install Docker if you don't have it installed already.
Run the following command to start the Unleash server:
 
```
docker run -p 4242:4242 unleashorg/unleash-server
```

This will start the Unleash server on port 4242.

Now that your Unleash server is up and running, you can access the Unleash UI by opening your web browser and navigating to http://localhost:4242.

To create a new feature flag in the Unleash UI, follow these steps:

Log in to the Unleash UI with the default credentials (username: admin, password: unleash4all).
Once logged in, click on the "Create toggle" button in the top-right corner of the page.
Fill in the required fields for your new feature flag:
Name: The unique name of the feature flag (e.g., my-new-feature).
Description: A brief description of the feature flag's purpose.
Enabled: Whether the feature flag is enabled or disabled by default.
Click the "Create" button to create your new feature flag.
You can now use this feature flag in your Spring Boot application by checking its status with the Unleash instance, as shown in the previous example:


```java
if (unleash.isEnabled("my-new-feature")) {
    // Feature flag is enabled, perform the new feature's behavior
} else {
    // Feature flag is disabled, perform the old behavior
}
```

Remember to replace "my-new-feature" with the actual name of the feature flag you created in the Unleash UI. The Unleash client in your Spring Boot application will fetch the feature flags from the Unleash server and cache them for efficient access.


## Sample to use Togglz in spring

To get started with Togglz in a Spring Boot application, follow these steps:

Add the Togglz Spring Boot Starter and Togglz Console dependencies to your pom.xml (Maven) or build.gradle (Gradle) file.
Maven:


```xml
<dependency>
    <groupId>org.togglz</groupId>
    <artifactId>togglz-spring-boot-starter</artifactId>
    <version>2.9.9</version>
</dependency>
<dependency>
    <groupId>org.togglz</groupId>
    <artifactId>togglz-console</artifactId>
    <version>2.9.9</version>
</dependency>
```

Define your feature flags by creating an enumeration that implements the Feature interface:
```java
public enum MyFeatures implements Feature {

    @Label("New Feature")
    NEW_FEATURE;

    public boolean isActive() {
        return FeatureContext.getFeatureManager().isActive(this);
    }
}
```

In this example, we have defined a single feature flag called NEW_FEATURE.

Configure Togglz in your application.properties or application.yml file:

```
togglz.console.enabled=true
togglz.console.path=/togglz-console
togglz.console.secured=false
```

togglz.feature-enums=your.package.MyFeatures
Replace your.package with the actual package where you defined the MyFeatures enumeration.

Use the feature flags in your application code:

```java
if (MyFeatures.NEW_FEATURE.isActive()) {
    // New feature is enabled, perform the new feature's behavior
} else {
    // New feature is disabled, perform the old behavior
}
```

Access the Togglz Console in your web browser:
After starting your Spring Boot application, open your web browser and navigate to http://localhost:8080/togglz-console. You'll see the Togglz Console, where you can manage the state of your feature flags.

By default, the Togglz Console is not secured, which means anyone can access it. In a production environment, you should secure the Togglz Console using Spring Security or another authentication mechanism. You can find more information on securing the Togglz Console in the official documentation: https://www.togglz.org/documentation/console.html.

## secure togglez
To secure the Togglz Console with Spring Security, follow these steps:

Add the Spring Security dependency to your pom.xml (Maven) or build.gradle (Gradle) file.
Maven:


```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

Create a configuration class that extends WebSecurityConfigurerAdapter to configure Spring Security.

```java
@Configuration
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/togglz-console/**").hasRole("ADMIN")
                .anyRequest().permitAll()
            .and()
            .formLogin()
                .defaultSuccessURL("/togglz-console", true)
            .and()
            .logout()
                .logoutSuccessUrl("/");
    }

    @Autowired
    public void configureGlobal(AuthenticationManagerBuilder auth) throws Exception {
        auth
            .inMemoryAuthentication()
                .withUser("admin").password(passwordEncoder().encode("admin123")).roles("ADMIN");
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

In this example, we have configured Spring Security to secure the /togglz-console path, requiring the user to have the "ADMIN" role to access it. We've also created an in-memory authentication user with the username "admin" and the password "admin123". The user has the "ADMIN" role, which allows access to the Togglz Console.

Please note that using in-memory authentication with hardcoded credentials is not recommended for production environments. Instead, you should use a proper authentication and authorization mechanism, such as connecting to a database or using OAuth2.

Restart your Spring Boot application and access the Togglz Console.
Now, when you navigate to http://localhost:8080/togglz-console, you will be prompted to log in with the configured credentials (username: admin, password: admin123). After logging in, you'll have access to the Togglz Console and can manage your feature flags securely.

Remember that this is just a basic example of securing the Togglz Console using Spring Security. You can further customize the security configuration to fit your specific requirements and use different authentication mechanisms as needed.


## customise togglez 

Now that you have secured the Togglz Console using Spring Security, you might want to explore more advanced features and configurations. Here are some additional ideas you can implement:

Customize the Togglz Console appearance: You can change the look and feel of the Togglz Console to match your application's branding by providing a custom CSS file. To do this, add the following property to your application.properties or application.yml file:

togglz.console.css=/path/to/your/custom.css
Replace /path/to/your/custom.css with the actual path to your custom CSS file.

Use a different feature state storage: By default, Togglz uses an in-memory feature state storage, which means that any changes to feature flags will be lost when the application restarts. To persist feature flag states, you can use other storage options such as a database or Redis. For example, to store feature flag states in a relational database, add the following dependencies to your pom.xml (Maven) or build.gradle (Gradle) file:
Maven:


```xml
<dependency>
    <groupId>org.togglz</groupId>
    <artifactId>togglz-jpa</artifactId>
    <version>2.9.9</version>
</dependency>
```

Then, configure the JPA feature state repository in one of your configuration classes:

```java
@Configuration
public class TogglzConfig {

    @Bean
    public FeatureProvider featureProvider() {
        return new EnumBasedFeatureProvider(MyFeatures.class);
    }

    @Bean
    public StateRepository stateRepository(DataSource dataSource) {
        return new JPAStateRepository(dataSource);
    }
}
```

Don't forget to configure a DataSource for your database connection.

Integrate Togglz with user management and authorization systems: In more complex applications, you might want to integrate Togglz with your existing user management and authorization systems to control which users have access to certain feature flags. Togglz provides a UserProvider interface that you can implement to achieve this integration. You can find more information about integrating Togglz with user management systems in the official documentation: https://www.togglz.org/documentation/user-management.html.
These are just a few examples of what you can do with Togglz in a Spring Boot application. Togglz is a versatile and extensible library that can be customized to fit a wide range of use cases. To explore more advanced configurations and features, refer to the official Togglz documentation: https://www.togglz.org/documentation/.

# best practice 

Now that you have a good understanding of Togglz, let's discuss some best practices and strategies for using feature flags effectively in your Spring Boot application:

 - Keep feature flags simple: The more complex your feature flags are, the harder it becomes to manage and understand them. Try to create simple, easy-to-understand feature flags that are focused on specific functionality.
 - Limit the scope of feature flags: When possible, use feature flags to control small, self-contained pieces of functionality. This will make it easier to reason about your application's behavior and reduce the chance of unintended side effects.
 - Use feature flags for temporary switches: Feature flags should ideally be used as temporary switches during the development and deployment process. Once a feature has been fully rolled out and tested, consider removing the feature flag and associated code to keep your codebase clean and maintainable.
 - Monitor and track feature flag usage: Keep track of which feature flags are active in your application, and monitor their impact on performance and user experience. This can help you identify and resolve issues related to feature flags more quickly.
 - Use a consistent naming convention: Adopt a consistent naming convention for your feature flags to make them easy to find and understand. A common approach is to use a prefix related to the feature or functionality, followed by a descriptive name (e.g., billing-new-invoice-system).
 - Plan for feature flag removal: As mentioned earlier, feature flags should ideally be temporary. Plan for their removal by setting deadlines or conditions for when a feature flag should be removed from the codebase. This helps prevent your application from accumulating technical debt and becoming difficult to maintain.
 - Document feature flags: Document the purpose and intended use of each feature flag in your application. This can help your team understand the rationale behind each flag and make it easier to manage and maintain them.
 - Test with feature flags: Make sure to include feature flags in your testing strategy. Test your application with different combinations of feature flags enabled and disabled to ensure that it behaves correctly under all conditions.


By following these best practices and strategies, you can effectively leverage feature flags in your Spring Boot application to manage feature rollouts, perform A/B testing, and more, while minimizing the potential risks and complexity associated with their use.

## activation strategies 

Here are some more advanced use cases and strategies for feature flags in your Spring Boot application:

 - A/B testing: Use feature flags to enable A/B testing in your application. By gradually rolling out a new feature to a percentage of your user base, you can gather feedback and metrics to determine the feature's impact and effectiveness. This allows you to make data-driven decisions about whether to roll out the feature to all users or make further adjustments.
 - Canary releases: Use feature flags to implement canary releases, where you deploy a new feature to a small subset of your user base before rolling it out more broadly. This can help you identify and resolve issues with the new feature before it impacts your entire user base.
 - Controlled rollouts: Use feature flags to roll out new features gradually, rather than all at once. This can help reduce the risk of introducing new issues and give you more control over the deployment process.
 - Kill switch: Implement a kill switch for critical features using feature flags. This allows you to quickly disable a feature if an issue arises, minimizing the impact on your users.
 - Environment-specific configurations: Use feature flags to enable or disable specific features based on the environment your application is running in. For example, you might want to enable a feature only in your staging environment for testing purposes.
 - Role-based access control: Use feature flags in conjunction with your application's user management and authorization system to control access to specific features based on user roles or permissions.
 - Custom activation strategies: Togglz and other feature flag libraries allow you to implement custom activation strategies. This enables you to control feature flag activation based on your specific business logic, such as user attributes, geographic location, or other factors.
 - Remember that while feature flags can provide significant benefits, they can also introduce complexity and risks if not managed properly. It's essential to follow best practices and have a well-defined process in place for creating, managing, and eventually removing feature flags from your application.

By using feature flags effectively and responsibly, you can gain more control over your application's development and deployment process, reduce risk, and improve your ability to respond to changing requirements and user feedback.

# reference 
https://www.togglz.org/documentation/admin-console.html
