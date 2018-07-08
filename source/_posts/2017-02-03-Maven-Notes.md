---
layout: page
title: Maven-Notes
tags:
- java
- maven
---
# Maven philosophy
- “It is important to note that in the pom.xml file you specify the what and not the how. The pom.xml file can also serve as a documentation tool, conveying your project dependencies and their versions.”


## Maven default repository

http://repo.maven.apache.org/maven2/

# Maven Settings
The settings element in the settings.xml file contains elements used to define values which configure Maven execution in various ways, like the pom.xml, but should not be bundled to any specific project, or distributed to an audience. These include values such as the local repository location, alternate remote repository servers, and authentication information.

There are two locations where a settings.xml file may live:

- The Maven install: ${maven.home}/conf/settings.xml
- A user’s install: ${user.home}/.m2/settings.xml
The former settings.xml are also called `global settings`, the latter settings.xml are referred to as user settings. If both files exists, their contents gets merged, with the user-specific settings.xml being dominant.

Tip: If you need to create user-specific settings from scratch, it’s easiest to copy the global settings from your Maven installation to your ${user.home}/.m2 directory. Maven’s default settings.xml is a template with comments and examples so you can quickly tweak it to match your needs.


## All Maven pom.xml inherits from super POM

# Coc: Convention over Configuration
- Convention over configuration is a simple concept. Systems, libraries, and frameworks should assume reasonable defaults without requiring that unnecessary configuration systems should “just work.” Popular frameworks such as Ruby on Rails and EJB3 have started to adhere to these principles in reaction to the configuration complexity of frameworks such as the initial Enterprise JavaBeans? (EJB) specifications. 
- “Popularized by the Ruby on Rails community, CoC emphasizes sensible defaults, thereby reducing the number of decisions to be made.”
- “Gradle’s flexibility, like that of Ant, can be abused, which results in difficult and complex builds.
”


# Notes
- This is the Project Object Model (POM), a declarative description of a project. 

## Coordinate
- “group, artifact, and version (**GAV**) coordinates”
- We’ve highlighted the Maven coordinates for this project: **groupId, artifactId, version and packaging. These combined identifiers make up a project’s coordinates**.[3] Just as in any other coordinate system, a Maven coordinate is an address for a specific point in “space”: from general to specific. Maven pinpoints a project via its coordinates when one project relates to another, either as a dependency, a plugin, or a parent project reference. 
- Maven coordinates are often written using a colon as a delimiter in the following format: **groupId:artifactId:packaging:version**. 
- Projects undergoing active development can use a special identifier that marks **a version as a SNAPSHOT**.
- The packaging format of a project is also an important component in the Maven coordinates, but it isn’t a part of a project’s unique identifiers. A project’s groupId:artifactId:version make that project unique; you can’t have a project with the same three groupId, artifactId, and version identifiers.
- **packaging: The type of project, defaulting to jar**, describing the packaged output produced by a project. A project with packaging jar produces a JAR archive; a project with packaging war produces a web application.
- The core of Maven is pretty dumb; it doesn’t know how to do much beyond parsing a few XML documents and keeping track of a lifecycle and a few plugins. Maven has been designed to delegate most responsibility to a set of Maven plugins that can affect the Maven lifecycle and offer access to goals. Most of the action in Maven happens in plugin goals that take care of things like compiling source, packaging bytecode, publishing sites, and any other task that needs to happen in a build. 
- You benefit from the fact that plugins are downloaded from a remote repository and maintained centrally. This is what is meant by universal reuse through Maven plugins.
- working developers are starting to realize that Maven not only simplifies the task of build management, it is helping to encourage a common interface between developers and software projects.

# Maven vs Ant
## The differences between Ant and Maven in this example are:
### Apache Ant 
Ant doesn’t have formal conventions such as a common project directory structure; you have to tell Ant exactly where to find the source and where to put the output. Informal conventions have emerged over time, but they haven’t been codified into the product.
- Ant is procedural; you have to tell Ant exactly what to do and when to do it. You have to tell it to compile, then copy, then compress.
- Ant doesn’t have a lifecycle; you have to define goals and goal dependencies. You have to attach a sequence of tasks to each goal manually.
### Apache Maven
- Maven has conventions: in the example, it already knew where your source code was because you followed the convention. It put the bytecode in target/classes, and it produced a JAR file in target.
- Maven is declarative; all you had to do was create a pom.xml file and put your source in the default directory. Maven took care of the rest.
- Maven has a lifecycle, which you invoked when you executed mvn install. This command told Maven to execute a series of sequence steps until it reached the lifecycle. As a side effect of this journey through the lifecycle, Maven executed a number of default plugin goals that did things such as compile and create a JAR.
- A Maven plugin is a collection of one or more goals (see Figure 3-1). Examples of Maven plugins can be simple core plugins such as the Jar plugin that contains goals for creating JAR files, the Compiler plugin that contains goals for compiling source code and unit tests, or the Surefire plugin that contains goals for executing unit tests and generating reports.

#### Maven life cycle
- The second command we ran in the previous section was **mvn install**. This command didn’t specify a plugin goal; instead, it specified a Maven lifecycle phase. A phase is a step in what Maven calls the “build lifecycle.” The build lifecycle is an ordered sequence of phases involved in building a project.
- **Plugin goals can be attached to a lifecycle phase**. As Maven moves through the phases in a lifecycle, it will execute the goals attached to each particular phase. Each phase may have zero or more goals bound to it. In the previous section, when you ran mvn install, you might have noticed that more than one goal was executed. Examine the output after running mvn install and take note of the various goals that are executed. 
- Maven steps through the phases preceding package in the Maven lifecycle; **executing a phase will first execute all proceeding phases in order**, ending with the phase specified on the command line. Each phase corresponds to zero or more goals, and since we haven’t performed any plugin configuration or customization, this example binds a set of standard plugin goals to the default lifecycle. 

# Dependency
- “Maven provides **declarative dependency management**. With this approach, you declare your project’s dependencies in an external file called pom.xml. Maven will automatically download those dependencies and hand them over to your project for the purpose of building, testing, or packaging.”
- “The default remote repository with which Maven interacts is called Maven Central, and it is located at repo.maven.apache.org and uk.maven.org.”
- “The **internal repository manager** acts as a proxy to remote repositories. Because you have full control over the internal repository, you can regulate the types of artifacts allowed in your company. Additionally, you can also push your organization’s artifacts onto the server, thereby enabling collaboration. ”, such as Nexus

## Transitive Dependcies
- “A key benefit of Maven is that it automatically “deals with transitive dependencies and includes them in your project.
- “Maven uses a technique known as **dependency mediation** to resolve version conflicts. Simply stated, dependency mediation allows Maven to pull the dependency that **is closest to the project in the tree**. In Figure 3-3, there are two versions of dependency B: 0.0.8 and 1.0.0. In this scenario, version 0.0.8 of dependency B is included in the project, because it is a direct dependency and closest to the tree. Now look at the three versions of dependency F: 0.1.3, 1.0.0, and 2.2.0. All three dependencies are at the same depth. In this scenario, Maven will use the **first-found dependency**, which would be 0.1.3, and not the latest 2.2.0 version.”

## Dependency Scope
- “Maven uses the concept of scope, which allows you to specify **when and where** you need a particular dependency.” “Maven provides the following six scopes:”
- “**compile**: Dependencies with the compile scope are available in the class path in all phases on a project build, test, and run. This is the default scope.”
- “**provided**: Dependencies with the provided scope are available in the class path during the build and test phases. They don’t get bundled within the generated artifact. Examples of dependencies that use this scope include Servlet api, JSP api, and so on.”
- “**runtime**: Dependencies with the runtime scope are not available in the class path during the build phase. Instead they get bundled in the generated artifact and are available during runtime.”
- “**test**: Dependencies with the test scope are available during the test phase. JUnit and TestNG are good examples of dependencies with the test scope.”
- “**system**: Dependencies with the system scope are similar to dependencies with the provided scope, except that these dependencies are not retrieved from the repository. Instead, a hard-coded path to the file system is specified from which the dependencies are used.”
- “**import**: The import scope is applicable for .pom file dependencies only. It allows you to include dependency management information from a remote .pom file. The import scope is available only in Maven 2.0.9 or later.”


# Setup Proxy
- “Maven requires an Internet connection to download plug-ins and dependencies. Some companies employ HTTP proxies to restrict access to the Internet. In those scenarios, running Maven will result in Unable to download artifact errors. To address this, edit the settings.xml file and add the proxy information specific to your company.”
```xml
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
                      http://maven.apache.org/xsd/settings-1.0.0.xsd">
  <proxies>
  <proxy>
      <id>companyProxy</id>
      <active>true</active>
      <protocol>http</protocol>
      <host>proxy.company.com</host>
      <port>8080</port>
      <username>proxyusername</username>
      <password>proxypassword</password>
      <nonProxyHosts />
    </proxy>
  </proxies>
 </settings>
```


# Multimodule projects
## Generate parent
```sh
mvn archetype:generate -DgroupId=com.apress.gswmbook -DartifactId=gswm-parent -Dversion=1.0.0-SNAPSHOT -DarchetypeGroupId=org.codehaus.mojo.archetypes -DarchetypeArtifactId=pom-root
```
Listing 6-5. Parent pom.xml File with Modules

```xml

<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.apress.gswmbook</groupId>
  <artifactId>gswm-parent</artifactId>
  <version>1.0.0-SNAPSHOT</version>
  <packaging>pom</packaging>
  <name>gswm-parent</name>
  <modules>
    <module>gswm-web</module>
    <module>gswm-service</module>
    <module>gswm-repository</module>
  </modules>
</project>
```
## Generate web module
```sh
mvn archetype:generate -DgroupId=com.todzhang.mywebApp -DartifactId=main-web -Dversion=1.0.0-SNAPSHOT -Dpackage=war -DarchetypeArtifactId=maven-archetype-webapp
```
```xml
<?xml version="1.0"?>
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns="http://maven.apache.org/POM/4.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>com.apress.gswmbook</groupId>
    <artifactId>gswm-parent</artifactId>
    <version>1.0.0-SNAPSHOT</version>
  </parent>
  <groupId>com.apress.gswmbook</groupId>
  <artifactId>gswm-web</artifactId>
  <version>1.0.0-SNAPSHOT</version>
  <packaging>war</packaging>
  <name>gswm-web Maven Webapp</name>
  <url>http://maven.apache.org</url>
  <dependencies>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>3.8.1</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <finalName>gswm-web</finalName>
  </build>
</project>
```
## Generate a service jar module
```sh
mvn archetype:generate -DgroupId=com.todzhang.mywebApp -DartifactId=back-service -Dversion=1.0.0-SNAPSHOT -DarchetypeArtifactId=maven-archetype-quickstart -DinteractiveMode=false
```
- Notice that you didn’t provide the package parameter, as the maven-archetype-quickstart produces a JAR project by default.
## To start the module
```sh
mvn packages
```
# Create archetype from project
```sh
mvn archetype:create-from-project
```
# Site life cycle
```sh
mvn site
```
- The site life cycle uses Maven’s site plug-in to generate the site for a single project. Once this command completes, a site folder gets created under the project’s target.
- Open the index.html file to browse the generated site. You will notice that Maven used the information provided in the pom.xml file to generate most of the documentation. It also automatically applied the default skin and generated the corresponding images and CSS files. 
- To regenerate site
```sh
mvn clean site
```

# JavaDoc
- Maven provides a Javadoc plug-in, which uses the Javadoc tool for generating Javadocs. Integrating the Javadoc plug-in simply involves declaring it in the reporting element of pom.xml file, as shown in Listing 7-4. Plug-ins declared in the pom reporting element are executed during site generation.
```xml
<project>
        <!—Content removed for brevity-->
 <reporting>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-javadoc-plugin</artifactId>
        <version>2.10.1</version>
      </plugin>
    </plugins>
  </reporting>
</project>
```
Then run **mvn clean site** to generate javadoc,  the apidocs folder created under gswm /target/site
# Unit test report
- Maven offers the Surefire plug-in that provides a uniform interface for running tests created by frameworks such as JUnit or TestNG. It also generates execution results in various formats such as XML and HTML. These published results enable developers to find and fix broken tests quickly.
The Surefire plug-in is configured in the same way as the Javadoc plug-in in the reporting section of the pom file. Listing 7-5 shows the Surefire plug-in configuration.
```xml
<project>
        <!—Content removed for brevity-->
  <reporting>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-report-plugin</artifactId>
        <version>2.17</version>
      </plugin>
    </plugins>
  </reporting>
</project>
```
-  you will see a Surefire Reports folder generated under gswm\target. It contains the test execution results in XML and TXT formats. The same information will be available in HTML format in the surefire-report.html file under site folder.

# Code coverate report
- Code coverage is a measurement of how much source code is being exercised by automated tests. Essentially, it provides an indication of the quality of your tests. Emma and Cobertura are two popular open source code coverage tools for Java.
In this section, you will use Cobertura for measuring this project’s code coverage. Configuring Cobertura is similar to other plug-ins, as shown in
```xml
<project>
        <!—Content removed for brevity-->
  <reporting>
    <plugins>
      <plugin>
        <groupId>org.codehaus.mojo</groupId>
        <artifactId>cobertura-maven-plugin</artifactId>
        <version>2.6</version>
      </plugin>
   </plugins>
  </reporting>
</project>
```
# Find bug reports
- FindBugs is a tool for detecting defects in Java code. It uses static analysis to detect bug patterns, such as infinite recursive loops and null pointer dereferences. Listing 7-7 shows the FindBugs configuration.

```xml
<project>
        <!—Content removed for brevity-->
  <reporting>
    <plugins>
      <plugin>
        <groupId>org.codehaus.mojo</groupId>
        <artifactId>findbugs-maven-plugin</artifactId>
        <version>3.0.0</version>
      </plugin>
   </plugins>
 </reporting>
</project>
```

# Integration with Nexus
-  Repository managers act as a proxy of public repositories, facilitate artifact sharing and team collaboration, ensure build stability, and enable the governance of artifacts used in the enterprise.
- Nexus is a popular open source repository manager from Sonatype. It is a web application that allows you to maintain internal repositories and access external repositories. It allows repositories to be grouped and accessed via a single URL. This enables the repository administrator to add and remove new repositories behind the scenes without requiring developers to change the configuration on their computers. Additionally, it provides hosting capabilities for sites generated using Maven site and artifact search capabilities.

## To enable nexus in Maven
- You will start by adding a distributionManagement element in the pom.xml file, as shown in Listing 8-1. This element is used to declare the location where the project’s artifacts will be when deployed. The repository element indicates the location where released artifacts will be deployed. Similarly, the snapshotRepository element identifies the location where the SNAPSHOT versions of the project will be stored.
```xml
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi=http://www.w3.org/2001/XMLSchema-instance” xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">  <modelVersion>4.0.0</modelVersion>

        <!-- Content removed for brevity -->
        <distributionManagement>
           <repository>
                <id>nexusReleases</id>
              <name>Releases</name>
        <url>http://localhost:8081/nexus/content/repositories/releases</url>
           </repository>
           <snapshotRepository>
              <id>nexusSnapshots</id>
              <name>Snapshots</name>
              <url>http://localhost:8081/nexus/content/repositories/snapshots</url>
           </snapshotRepository>
        </distributionManagement>
<!-- Content removed for brevity -->
</project>
```
- Out of the box, Nexus comes with **Releases and Snapshots repositories**. By default, SNAPSHOT artifacts will be stored in the Snapshots Repository, and release artifacts will be stored in the Releases repository.
Like most repository managers, deployment to Nexus is a protected operation. You provide the credentials needed to interact with Nexus in the **settings.xml** file.
- Listing 8-2. Settings.xml File with Server Information
- Listing 8-2 shows the settings.xml file with the server information. The Nexus deployment user with password deployment123 is provided out of the box. Notice that the IDs declared in the server tag — nexusReleases and nexusSnapshots must match the IDs of the repository and snapshotRepository declared in the pom.xml file. Replace the contents of the settings.xml file in the C:\Users\<<USER_NAME>>\.m2 folder with the code in Listing 8-2.
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">
<servers>
   <server>
      <id>nexusReleases</id>
      <username>deployment</username>
      <password>deployment123</password>
   </server>
   <server>
      <id>nexusSnapshots</id>
      <username>deployment</username>
      <password>deployment123</password>
   </server>
</servers>
</settings>
```
- This concludes the configuration steps for interacting with Nexus. At the command line, run the command mvn deploy under the directory C:\apress\gswm-book\chapter8\gswm. Upon successful execution of the command, you will see the SNAPSHOT artifact under Nexus 
