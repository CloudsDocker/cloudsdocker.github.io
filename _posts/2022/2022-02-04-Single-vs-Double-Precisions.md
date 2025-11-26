---
header:
    image: /assets/images/hd_mvn_skip_tests.png
title:  Single vs Double precisions, float vs double data type
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

# precision matters

 - Double precision provides greater range (approximately 10**(-308) to 10 ** 308) and precision (about **15 decimal** digits) than single precision (approximate range 10**(-38) to 10 ** 38, with about **7 decimal** digits of precision).
 - Computations that mix single and double operands are performed in double precision, which requires conversion of the single-precision operands to double-precision. These conversions do not affect performance.



https://sample.com/display/FMP/MavenReportException%3A+Error+while+generating+Javadoc






Symptoms
When running project install, one error "Failed to execute goal org.apache.maven.plugins:maven-javadoc-plugin:3.3.1:jar (attach-javadocs) on project" raised. The Error summary is

Failed to execute goal org.apache.maven.plugins:maven-javadoc-plugin:3.3.1:jar (attach-javadocs) 

Error stack trace as below

[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [INFO] Reactor Summary for pretrade-partymodel-server 1.0.0:
[INFO] [INFO]
[INFO] [INFO] pretrade-partymodel-server ......................... SUCCESS [ 3.791 s]
[INFO] [INFO] ptt-client-partymodel-service-dto .................. FAILURE [ 4.718 s]
[INFO] [INFO] ptt-client-partymodel-service ...................... SKIPPED
[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [INFO] BUILD FAILURE
[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [INFO] Total time: 8.750 s
[INFO] [INFO] Finished at: 2021-11-10T12:38:50+11:00
[INFO] [INFO] ------------------------------------------------------------------------
[INFO] [ERROR] Failed to execute goal org.apache.maven.plugins:maven-javadoc-plugin:3.3.1:jar (attach-javadocs) on project ptt-client-partymodel-service-dto: MavenReportException: Error while generating Javadoc:
[INFO] [ERROR] Exit code: 1 - javadoc: error - The code being documented uses modules but the packages defined in https://docs.oracle.com/javase/8/docs/api/ are in the unnamed module.
[INFO] [ERROR]
[INFO] [ERROR] Command line was: /usr/lib/jvm/java-11-openjdk-amd64/bin/javadoc -J-Dhttps.proxyHost=localhost -J-Dhttps.proxyPort=3128 -J-Dhttp.proxyHost=localhost -J-Dhttp.proxyPort=3128 "-J-Dhttp.nonProxyHosts=\"localhost^|10.^|.sample.com^|.btfin.com^|.thewestpacgroup.com.au^|snow.thewestpacgroup.com.au^|127.0.0.1^|nexus.fx.srv.westpac.com.au\"" @options @packages
[INFO] [ERROR]
[INFO] [ERROR] Refer to the generated Javadoc files in '/mnt/c/local/git/ptc/pretrade-partymodel-server/target/checkout/ptt-client-partymodel-service-dto/target/apidocs' dir.
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



