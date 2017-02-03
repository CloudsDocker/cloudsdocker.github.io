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