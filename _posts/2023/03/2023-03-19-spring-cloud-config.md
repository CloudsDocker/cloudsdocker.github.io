---
title: Spring Cloud Master Piece 9
header:
image: /assets/images/yarn_npm_install.jpg
date: 2023-03-19
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/spring_cloud_master_piece_9
layout: single
category: tech
---


# What’s spring cloud config
Spring Cloud Config is a distributed configuration server that provides a centralized location to manage external properties for applications across all environments. It is part of the Spring Cloud family of tools that help developers build microservices-based applications.

With Spring Cloud Config, you can store configuration files in a Git repository, SVN, or a local file system. These configuration files can then be accessed by multiple microservices in different environments (e.g., development, staging, and production) to maintain consistency in the configuration. You can also use Spring Cloud Config to manage sensitive information, such as passwords or API keys, by encrypting the configuration data.

Spring Cloud Config supports a range of formats, including YAML, JSON, Properties, and XML. It also provides a REST API that allows applications to access configuration properties programmatically.

One of the key benefits of using Spring Cloud Config is that it makes it easy to manage configuration changes across multiple environments. Developers can make changes to the configuration files in the central repository and those changes are propagated to all the microservices that use them. This makes it easy to manage configuration changes, reducing the risk of configuration errors that can lead to application downtime.

Overall, Spring Cloud Config is a powerful tool for managing configuration in microservices-based applications, and it can help streamline development and deployment processes, reduce errors, and improve overall application reliability.

# Spring Cloud Config Setup sample

here's an example of a basic Spring Cloud Config setup:

Create a new Spring Boot project and add the following dependencies to your pom.xml file:
xml
Copy code
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-config-server</artifactId>
</dependency>
Add the @EnableConfigServer annotation to your main Spring Boot application class.
java
Copy code
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.config.server.EnableConfigServer;

@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }

}
Create a Git repository to store your configuration files. In this example, we'll use GitHub as our Git repository hosting service.
Create a application.yml file in your Git repository to store your configuration properties:
yaml
Copy code
server:
  port: 8888

spring:
  cloud:
    config:
      server:
        git:
          uri: https://github.com/{username}/{repository}.git
          search-paths: {directory}/{filename}
Replace {username}, {repository}, {directory} and {filename} with your own values.

Start your Spring Boot application and verify that the configuration server is running by accessing the following URL in your web browser:
javascript
Copy code
http://localhost:8888/{application}/{profile}
Replace {application} and {profile} with the names of your application and profile respectively. This should return the configuration properties stored in your Git repository.



# client application 

Now, you can create a client application that connects to the Spring Cloud Config server to retrieve its configuration. Add the following dependencies to your client application's pom.xml file:
xml
Copy code
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-config</artifactId>
</dependency>
Create a bootstrap.yml file in your client application's src/main/resources directory with the following content:
yaml
Copy code
spring:
  application:
    name: {application}
  cloud:
    config:
      uri: http://localhost:8888
      profile: {profile}
      label: master
Replace {application} and {profile} with the names of your application and profile respectively.

Create a configuration file for your client application in your Git repository. The file name should be {application}-{profile}.yml, where {application} and {profile} are the names of your client application and profile respectively. For example, if your client application is named my-app and the profile is dev, the file name should be my-app-dev.yml.
Start your client application and verify that it's retrieving its configuration from the Spring Cloud Config server. You can do this by logging the configuration properties in your client application's main class.
java
Copy code
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class MyAppApplication {

    public static void main(String[] args) {
        SpringApplication.run(MyAppApplication.class, args);
    }

}

@RestController
@RefreshScope
class ConfigController {

    @Value("${my.property}")
    private String myProperty;

    @GetMapping("/my-property")
    public String getMyProperty() {
        return myProperty;
    }

}
Now, when you access http://localhost:8080/my-property in your web browser, you should see the value of my.property from your configuration file. If you change the value of my.property in your Git repository and call the /actuator/refresh endpoint on your client application, the new value will be loaded without restarting the client application.


# encrypted config properties

You can also use Spring Cloud Config's encryption and decryption features to secure sensitive configuration properties. To do this, you need to generate a public-private key pair and add the public key to your Git repository. You can generate the key pair using the keytool command line tool:
lua
Copy code
keytool -genkeypair -alias config-server-key -keyalg RSA -dname "CN=Config Server,OU=Spring,O=Pivotal,L=Los Gatos,S=California,C=US" -keypass mysecretpassword -keystore config-server.jks -storepass mysecretpassword
Replace mysecretpassword with your own password. This command will generate a key pair and store it in a Java KeyStore file named config-server.jks.

Add the following properties to your Spring Cloud Config server's application.yml file to enable encryption and decryption:
yaml
Copy code
encrypt:
  key-store:
    location: classpath:/config-server.jks
    password: mysecretpassword
    alias: config-server-key
    secret: mysecretpassword
Replace mysecretpassword with your own password. This will configure Spring Cloud Config to use the config-server.jks file as its key store and the config-server-key alias as its key for encryption and decryption.

Encrypt the sensitive configuration properties in your client application's configuration file using the encrypt endpoint of your Spring Cloud Config server. You can do this using the curl command line tool:
bash
Copy code
curl localhost:8888/encrypt -d mysecretpassword
Replace mysecretpassword with your own sensitive value. This command will encrypt the value using the public key stored in your Git repository and return the encrypted value.

Replace the sensitive value in your client application's configuration file with the encrypted value.
Start your client application and verify that it's able to decrypt the sensitive configuration property using the private key stored in the key store of your Spring Cloud Config server. You can do this by logging the decrypted value in your client application's main class.
java
Copy code
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.encrypt.Encryptors;
import org.springframework.security.crypto.encrypt.TextEncryptor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class MyAppApplication {

    public static void main(String[] args) {
        SpringApplication.run(MyAppApplication.class, args);
    }

    @Bean
    public TextEncryptor textEncryptor() {
        return Encryptors.text("mysecretpassword", "0123456789ABCDEF");
    }

}

@RestController
@RefreshScope
class ConfigController {

    @Value("${my.encrypted.property}")
    private String myEncryptedProperty;

    @Value("${my.sensitive.property}")
    private String mySensitiveProperty;

    @Value("${my.property}")
    private String myProperty;

    private final TextEncryptor textEncryptor;

    public ConfigController(TextEncryptor textEncryptor) {
        this.textEncryptor = textEncryptor;
    }

    @GetMapping("/my-encrypted-property")
    public String getMyEncryptedProperty() {
        return myEncryptedProperty;
    }

    @GetMapping("/my-sensitive-property")
    public String getMySensitiveProperty() {
        return textEncryptor.decrypt(myEncryptedProperty);
    }

    @GetMapping("/my-property")
    public String getMyProperty() {
        return myProperty;
    }

}


# refresh
 

Use the @RefreshScope annotation to enable the configuration properties to be refreshed without restarting the client application. Add the following dependencies to your client application's pom.xml file to enable the Spring Boot Actuator endpoints:
xml
Copy code
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-config</artifactId>
  </dependency>
</dependencies>
Add the following properties to your client application's application.yml file to configure it to use the Spring Cloud Config server:
yaml
Copy code
spring:
  application:
    name: myapp
  cloud:
    config:
      uri: http://localhost:8888
      username: myuser
      password: mypassword
Replace myuser and mypassword with your own credentials.

Add the following annotation to your client application's main class to enable the use of the Spring Cloud Config server:
java
Copy code
@EnableConfigServer
@SpringBootApplication
public class MyAppApplication {

    public static void main(String[] args) {
        SpringApplication.run(MyAppApplication.class, args);
    }

}
Start your client application and verify that it's able to retrieve the configuration properties from the Spring Cloud Config server. You can do this by calling the /my-sensitive-property endpoint of your client application and verifying that it returns the decrypted value of the sensitive property.
That's it! You've now successfully set up a Spring Cloud Config server and client application, and you've learned how to use Spring Cloud Config to manage your application's configuration properties in a centralized and secure way.

# client application to use spring configuration 
Here's a sample configuration for a Spring Cloud Config Client:

Add the following dependency to your project's pom.xml file:
xml
Copy code
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-config</artifactId>
</dependency>
Add the following properties to your project's bootstrap.yml file:
yaml
Copy code
spring:
  application:
    name: your-application-name
  cloud:
    config:
      uri: http://localhost:8888
      username: your-username
      password: your-password
      fail-fast: true
Replace your-application-name, your-username, and your-password with your own values. The fail-fast property is optional and can be used to force the client to fail immediately if it cannot connect to the Spring Cloud Config server.

Create a configuration file for your application in the Git repository that's being used by the Spring Cloud Config Server. The file should be named {your-application-name}.yml and should contain your application's configuration properties.
For example, if your application name is my-application, create a file named my-application.yml in the Git repository and add your configuration properties to it.

Inject your configuration properties into your application using Spring's @Value annotation. For example:
java
Copy code
@RestController
public class MyController {

    @Value("${my.property}")
    private String myProperty;

    @GetMapping("/my-property")
    public String getMyProperty() {
        return myProperty;
    }

}
In this example, the value of the my.property configuration property is injected into the myProperty field using the @Value annotation.

Start your application and verify that it's able to retrieve its configuration properties from the Spring Cloud Config Server. You can do this by calling the /my-property endpoint of your application and verifying that it returns the value of the my.property configuration property.
That's it! You've now successfully configured a Spring Cloud Config Client to retrieve its configuration properties from a Spring Cloud Config Server.



