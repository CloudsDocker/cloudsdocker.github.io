Sample me to use Togglz in spring

To get started with Togglz in a Spring Boot application, follow these steps:

Add the Togglz Spring Boot Starter and Togglz Console dependencies to your pom.xml (Maven) or build.gradle (Gradle) file.
Maven:

xml
Copy code
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
Gradle:

groovy
Copy code
implementation 'org.togglz:togglz-spring-boot-starter:2.9.9'
implementation 'org.togglz:togglz-console:2.9.9'
Define your feature flags by creating an enumeration that implements the Feature interface:
java
Copy code
public enum MyFeatures implements Feature {

    @Label("New Feature")
    NEW_FEATURE;

    public boolean isActive() {
        return FeatureContext.getFeatureManager().isActive(this);
    }
}
In this example, we have defined a single feature flag called NEW_FEATURE.

Configure Togglz in your application.properties or application.yml file:
properties
Copy code
togglz.console.enabled=true
togglz.console.path=/togglz-console
togglz.console.secured=false

togglz.feature-enums=your.package.MyFeatures
Replace your.package with the actual package where you defined the MyFeatures enumeration.

Use the feature flags in your application code:
java
Copy code
if (MyFeatures.NEW_FEATURE.isActive()) {
    // New feature is enabled, perform the new feature's behavior
} else {
    // New feature is disabled, perform the old behavior
}
Access the Togglz Console in your web browser:
After starting your Spring Boot application, open your web browser and navigate to http://localhost:8080/togglz-console. You'll see the Togglz Console, where you can manage the state of your feature flags.

By default, the Togglz Console is not secured, which means anyone can access it. In a production environment, you should secure the Togglz Console using Spring Security or another authentication mechanism. You can find more information on securing the Togglz Console in the official documentation: https://www.togglz.org/documentation/console.html.
