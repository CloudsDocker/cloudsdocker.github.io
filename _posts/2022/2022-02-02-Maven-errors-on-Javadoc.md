---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  SkipTest-Not-Work-In-Multiple-models-project
date: 2022-02-02
tags:
 - Maven
 - Java
 - Errors
 
permalink: /blogs/tech/en/mvn_failed_to_skip_tests_in_multiple_modules_project
layout: single
category: tech
---

> Leave nothing for tomorrow which can be done today. -Abraham Lincoln.

# Golden rule for Maven issues & fix

The first and most important trick for Maven troubleshooting & fix is : 
(1) right click "pom.xml"
(2) Chose "reload project"
Rather than run mvn clean install 


# How to find the effective or settins in use

```bash
mvn help:effective-settings
```

# errors

## Formatting violation found. Failed to execute goal spring.javaformat:sprint-javaformat-maven-plugin

Error as below screenshot

![](/assets/images/maven_errors_javadocs.png)

### Solution
To fix those format error, run following one
```bash
mvn spring-javaformat:apply
```

## Failed to install-node-and-yarn

[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal com.github.eirslett:frontend-maven-plugin:1.10.0:install-node-and-yarn (install node and yarn) on project start-client: Could not download Node.js: Could not download https://nodejs.org/dist/v12.13.0/node-v12.13.0-linux-x64.tar.gz: nodejs.org:443 failed to respond -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.





#  Could not download Yarn: Could not download https://github.com/yarnpkg/yarn/releases/download/v1.22.4/yarn-v1.22.4.tar.gz: Connection reset -

[ERROR] Failed to execute goal com.github.eirslett:frontend-maven-plugin:1.10.0:install-node-and-yarn (install node and yarn) on project start-client: Could not download Yarn: Could not download https://github.com/yarnpkg/yarn/releases/download/v1.22.4/yarn-v1.22.4.tar.gz: Connection reset -> [Help 1]
org.apache.maven.lifecycle.LifecycleExecutionException: Failed to execute goal com.github.eirslett:frontend-maven-plugin:1.10.0:install-node-and-yarn (install node and yarn) on project start-client: Could not download Yarn: Could not download https://github.com/yarnpkg/yarn/releases/download/v1.22.4/yarn-v1.22.4.tar.gz


# Symptoms
When running project install, one error "Failed to execute goal org.apache.maven.plugins:maven-javadoc-plugin:3.3.1:jar (attach-javadocs) on project" raised. The Error summary is

Failed to execute goal org.apache.maven.plugins:maven-javadoc-plugin:3.3.1:jar (attach-javadocs) 

Error stack trace as below

[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [INFO] Reactor Summary for pretrade-partymodel-server 1.0.0:
[INFO] [INFO]
[INFO] [INFO] pretrade-partymodel-server ......................... SUCCESS [ 3.791 s]
[INFO] [INFO] org-test-client-service-dto .................. FAILURE [ 4.718 s]
[INFO] [INFO] org-test-client-service ...................... SKIPPED
[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [INFO] BUILD FAILURE
[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [INFO] Total time: 8.750 s
[INFO] [INFO] Finished at: 2021-11-10T12:38:50+11:00
[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [ERROR] Failed to execute goal org.apache.maven.plugins:maven-javadoc-plugin:3.3.1:jar (attach-javadocs) on project org-test-client-service-dto: MavenReportException: Error while generating Javadoc:
[INFO] [ERROR] Exit code: 1 - javadoc: error - The code being documented uses modules but the packages defined in https://docs.oracle.com/javase/8/docs/api/ are in the unnamed module.
[INFO] [ERROR]
[INFO] [ERROR] Command line was: /usr/lib/jvm/java-11-openjdk-amd64/bin/javadoc -J-Dhttps.proxyHost=localhost -J-Dhttps.proxyPort=3128 -J-Dhttp.proxyHost=localhost -J-Dhttp.proxyPort=3128 "-J-Dhttp.nonProxyHosts=\"localhost^|10.^|.abcde.com.au^|.btfin.com^|.theabcdegroup.com.au^|snow.theabcdegroup.com.au^|127.0.0.1^|nexus.fx.srv.abcde.com.au\"" @options @packages
[INFO] [ERROR]
[INFO] [ERROR] Refer to the generated Javadoc files in '/mnt/c/local/git/org/pretrade-partymodel-server/target/checkout/org-test-client-service-dto/target/apidocs' dir.
[INFO] [ERROR] -> [Help 1]


Error message screenshot


Solution


Please check following points for troubleshooting & problem solving  :

Most important one - release.properties  should NOT checked in.  This file should not used in local  environment. Here is details of this file.

The release:perform goal requires a file called release.properties to be present within the project root directory. The release.properties file is constructed during the execution of the release:prepare goal and contains all the information needed to locate and extract the correctly tagged version of the project. Shown below is an example of the contents that can appear within an instance of the release.properties file.

Make sure the setting to ignore errors in the javadoc plugin is on:  

<failOnError>false</failOnError>
Javadoc plugin should setup correctly. In other words, It should in parent's pluginManagement  (rather than under build plugins )  

<pluginManagement>
  <plugins>
    <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-javadoc-plugin</artifactId>
        <version>${maven-javadoc-plugin.version}</version>
        <configuration>
            <failOnError>false</failOnError>
            <source>8</source>
            <doclint>none</doclint>
        </configuration>
    </plugin>
 
  </plugins>
</pluginManagement>
While in children project, keep plugin config in simplest mode, no "versions", no 'configurations", such as 

    <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-javadoc-plugin</artifactId>
   </plugin>
</plugins>
Make sure JDK version consistency, e.g. If you added <source>8</source> to javadoc plugin - while the built/run with Java 11 will be incorrect 

To check whether goals prepare had run but goal perform failed leaving it half done

In pom.xml SCM  section, replace <tag>${project.version}</tag>  with <tag>HEAD</tag>  . This will be used in maven goal release:prepare 

It's better not to specify repositories as well as distributionManagement . Check out what's difference at Maven Blog: repositories vs DistributionRepostiory





Noteworthy points
Don't do the release locally. As it will generate release.properties which would cause failure of next goal "release:perform" failure locally.

















-------------


# Background & symptoms

As you know, you can skip tests during maven run, which maybe because you want to get an urgent task down or test will result in some noisy.

You alreay know, you can run following command to skip test

```java
mvn install -DskipTests
```
# Failures!
However, this skipTest won't work for project with `multiple modules`, for example if you run above command in **parent** module, each child project will still trigger *test* phase. 

To solve the problem, please use following command alternatively. 

Specifically, it's **-Darguments=-DskipTests**

```bash
mvn -Darguments=-DskipTests install
```

--End--



