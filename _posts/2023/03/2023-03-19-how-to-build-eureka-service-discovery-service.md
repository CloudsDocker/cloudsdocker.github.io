Sample me how to build a eureka service discovery

Sure! Here's a sample project that demonstrates how to build a Eureka service discovery server using Spring Boot:

Create a new Spring Boot project using your preferred IDE or the Spring Initializr.
Add the Eureka server dependency to your project's build file. You can do this by adding the following line to your pom.xml file if you are using Maven:
php
Copy code
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
</dependency>
Add the @EnableEurekaServer annotation to your application class to enable the Eureka server.
less
Copy code
@SpringBootApplication
@EnableEurekaServer
public class EurekaServiceDiscoveryApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServiceDiscoveryApplication.class, args);
    }
}
Configure your Eureka server by adding the following properties to your application.properties or application.yml file:
javascript
Copy code
server.port=8761

eureka.client.register-with-eureka=false
eureka.client.fetch-registry=false
eureka.client.service-url.defaultZone=http://localhost:8761/eureka/
In the above example, we're configuring the server to run on port 8761 and to use the same URL for the Eureka server registry as the server itself.

Run your Eureka server and verify that it is working correctly by navigating to the Eureka dashboard in your web browser at http://localhost:8761. You should see a list of registered applications and their status.
That's it! Your Eureka service discovery server is now up and running. You can now register your other microservices with this server and use it for service discovery. To register a microservice with the Eureka server, you can add the spring-cloud-starter-netflix-eureka-client dependency to the microservice project and configure it with the URL of the Eureka server.
