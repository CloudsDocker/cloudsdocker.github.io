---
header:
    image: /assets/images/hd_booster_does3.png
title:  Maven error and solution on No such host is known 
date: 2022-01-27
tags:
 - Maven
 - Java
 - Errors
 
permalink: /blogs/tech/en/mvn_failed_to_execute_goal_no_such_host_is_known
layout: single
category: tech
---

> Don't promis when you are hapy. Don't reply when you're angry and don't decide when you're sad
Service keep on restarting
If you spot service is restarting repeatedly. This is very likely caused by health probe detected unhealthy of service. Here are two practicable self-test .

Is Probe installed correctly?
Manually check probe
Test it in postman via following URL pattern:

https://sample.com:3799/pretrade/ptt-notification-service/actuator/health



Then check the response, ideally it should show as UP  and liveness , readiness  As below screenshot





Alternatively, the probe status can be tested and checked in application logs.

Check probe in logs
Firstly check logs in LENS or ELK, to maker sure you can see keyword /actuator  output in log, as below highlight in screenshot











The probe is installed as a specific Spring Actuator dependency in your project pom.xml



Spring Boot Actuator is a sub-project of the Spring Boot Framework. It includes a number of additional features that help us to monitor and manage the Spring Boot application. It contains the actuator endpoints (the place where the resources live).





<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
</dependencies>


Does Probe activated successfully?


Make sure to set WebApplicationType  NOT as NONE , otherwise aforesaid probe won't be activated. You can chose  or

org\springframework\boot\spring-boot\2.5.3\spring-boot-2.5.3-sources.jar!\org\springframework\boot\WebApplicationType.java



From your main java class, your code should similar to following:

        app.setWebApplicationType(WebApplicationType.SERVLET);
//        app.setWebApplicationType(WebApplicationType.NONE);


Technical background
Probe is one Springboot production readiness feature, which is controlled by WebApplicationType indirectly. This enum contains following valid list




/**
* The application should not run as a web application and should not start an
* embedded web server.
*/
NONE,

/**
* The application should run as a servlet-based web application and should start an
* embedded servlet web server.
*/
SERVLET,

/**
* The application should run as a reactive web application and should start an
* embedded reactive web server.
*/
REACTIVE;



Default value for WebApplicationType



Please be careful to leave it to default, as SpringBoot will trying to guess  default WebApplicationType based on runtime, it will call  deduceFromApplicationContext



For application loaded with Web libraries, it will set it as SERVLET  (rather than REACTIVE and NONE)



Sets the type of Spring ApplicationContext that will be created. If not specified defaults to DEFAULT_SERVLET_WEB_CONTEXT_CLASS for web based applications or AnnotationConfigApplicationContext for non web based applications.



-===============

















# Background & symptoms
One of most found error is `Failed to execute goal on project xxx` when you run 

```bash
mvn install
```

For example, below is error screenshot and mesage details

![](/assets/images/maven_error_no_host_known.png)

Please be advised the error wording **Failed to execute goal** on project abc-project-client: **Could not resolve dependencies for project** com.abc.dmy.

```bash
[ERROR] Failed to execute goal on project abc-project-client: Could not resolve dependencies for project com.abc.dmy.client:abc-client-code:jar:2.0.0-SNAPSHOT: Failed to collect dep
endencies at com.abc.client:abc-client-test:jar:2.0.0-SNAPSHOT -> com.abc.dmy.client:dmy-client-common:jar:2.0.0-SNAPSHOT: Failed to read artifact descriptor for com.abc.dmy.
client:dmy-client-common:jar:2.0.0-SNAPSHOT: Could not transfer artifact io.micrometer:micrometer-bom:pom:1.3.1 from/to central (https://repo.maven.apache.org/maven2): transfer failed for ht
tps://repo.maven.apache.org/maven2/io/micrometer/micrometer-bom/1.3.1/micrometer-bom-1.3.1.pom, proxy: ProxyInfo{host='abc-proxy.prod.brx.abc.com/', userName='null', port=8080, type='h
ttps', nonProxyHosts='null'}: No such host is known (abc-proxy.prod.brx.abc.com/) -> [Help 1]
[ERROR]
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR]
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/DependencyResolutionException

```


## Troubleshooting
`What done is done`, we are facing errors, what shall we do? To debug and fix an issue, firstly we'd `stay calm and keep on debuging`.

![](/assets/images/keep-calm-and-debug-it.png)

As you already know, if you'd like to know **rootcause of error**, firslty to drilldown to get more error details. You can run following command to output verbose logs

```bash
mvn -X install -l mvnOutput.log
```
## Explained
`-X` indicate this is for **debug**
`-l mvnOutput.log` denote output of this maven command to saved in file called *mvnOutput.log* 

Here are more details extract in above output, check the words **No such host is known**

```bash

Caused by: java.net.UnknownHostException: No such host is known (dmy-proxy.prod.abc.com/)
    at java.net.Inet6AddressImpl.lookupAllHostAddr (Native Method)
    at java.net.InetAddress$PlatformNameService.lookupAllHostAddr (InetAddress.java:929)
    at java.net.InetAddress.getAddressesFromNameService (InetAddress.java:1519)
    at java.net.InetAddress$NameServiceAddresses.get (InetAddress.java:848)
    at java.net.InetAddress.getAllByName0 (InetAddress.java:1509)
    at java.net.InetAddress.getAllByName (InetAddress.java:1368)
    at java.net.InetAddress.getAllByName (InetAddress.java:1302)
    at org.apache.maven.wagon.providers.http.httpclient.impl.conn.SystemDefaultDnsResolver.resolve (SystemDefaultDnsResolver.java:45)
    at org.apache.maven.wagon.providers.http.httpclient.impl.conn.DefaultHttpClientConnectionOperator.connect (DefaultHttpClientConnectionOperator.java:112)
    at org.apache.maven.wagon.providers.http.httpclient.impl.conn.PoolingHttpClientConnectionManager.connect (PoolingHttpClientConnectionManager.java:376)
    at org.apache.maven.wagon.providers.http.httpclient.impl.execchain.MainClientExec.establishRoute (MainClientExec.java:401)
    at org.apache.maven.wagon.providers.http.httpclient.impl.execchain.MainClientExec.execute (MainClientExec.java:236)
    at org.apache.maven.wagon.providers.http.httpclient.impl.execchain.ProtocolExec.execute (ProtocolExec.java:186)
    at org.apache.maven.wagon.providers.http.httpclient.impl.execchain.RetryExec.execute (RetryExec.java:89)
    at org.apache.maven.wagon.providers.http.httpclient.impl.execchain.RedirectExec.execute (RedirectExec.java:110)
    at org.apache.maven.wagon.providers.http.httpclient.impl.client.InternalHttpClient.doExecute (InternalHttpClient.java:185)
    at org.apache.maven.wagon.providers.http.httpclient.impl.client.CloseableHttpClient.execute (CloseableHttpClient.java:83)
    at org.apache.maven.wagon.providers.http.wagon.shared.AbstractHttpClientWagon.execute (AbstractHttpClientWagon.java:1005)
```

# Could not transfer artifact

There is another error similar to above error, so here I'll demonstrate , you may encounter this very likely down the roads.

Check out the error text `ArtifactTransferException: Could not transfer artifact`, then move on you'll find `SocketException: Connection reset`

```bash
Caused by: org.eclipse.aether.transfer.ArtifactTransferException: Could not transfer artifact io.micrometer:micrometer-bom:pom:1.3.1 from/to central (https://repo.maven.apache.org/maven2): transfer failed for https://repo.maven.apache.org/maven2/io/micrometer/micrometer-bom/1.3.1/micrometer-bom-1.3.1.pom, proxy: ProxyInfo{host='proxy.stgeorge.com', userName='null', port=8080, type='https', nonProxyHosts='null'}
    at org.eclipse.aether.connector.basic.ArtifactTransportListener.transferFailed (ArtifactTransportListener.java:52)
    at org.eclipse.aether.connector.basic.BasicRepositoryConnector$TaskRunner.run (BasicRepositoryConnector.java:369)
    at org.eclipse.aether.util.concurrency.RunnableErrorForwarder$1.run (RunnableErrorForwarder.java:75)
    at org.eclipse.aether.connector.basic.BasicRepositoryConnector$DirectExecutor.execute (BasicRepositoryConnector.java:628)


...
Caused by: java.net.SocketException: Connection reset
    at java.net.SocketInputStream.read (SocketInputStream.java:186)
    at java.net.SocketInputStream.read (SocketInputStream.java:140)
    at org.apache.maven.wagon.providers.http.httpclient.impl.io.SessionInputBufferImpl.streamRead (SessionInputBufferImpl.java:137)
```



# Troubleshooting & Solutions
Essentially all above errors are related to *network connection*, more precisely, it caused by **incorrect proxy host setup**. So the fix is straitforward, check and rectify your proxy configuration. 

## Guide to fix maven proxy errors

### Firstly know where or which settings.xml in used for Maven
Run following command first
```bash
mvn -X install -l mvnOutput.log
```

### Open maven output file and search following keyword
So you'll find the path to the *real* setting.xml in use

```bash
[DEBUG] Reading global settings from c:\dev\apache-maven-3.8.1\bin\..\conf\settings.xml
[DEBUG] Reading user settings from C:\Users\userSpiderMan\.m2\settings.xml
```
### Edit settings.xml to get the proxy host declared

Open the settings.xml found in previous step, normally it'd the file settings.xml under maven conf folder

Check proxy host settings under element `<proxy>`, for example, make sure the url in `host` is reachable


```xml
<proxies>
	<proxy>
			<id>abcCorpProxySSL</id>
			<active>true</active>
			<protocol>https</protocol>
			<username>username-aaa</username>
			<password>xxxx</password>
			<host>df.proxy.prod.abc.com</host>
            <!-- <host>proxy.abc.com</host> -->
			<!-- <host>dmy-proxy.prod.abc.com/</host> -->
			<port>8080</port>
			<nonProxyHosts>localhost|10.|.btfin.com|.theabcgroup.com|snow.theabcgroup.com|127.0.0.1|nexus.fx.srv.abc.com</nonProxyHosts>
		</proxy>
		
    </proxies>
```

### Update to your workable proxy setup and retry
Once you changed host, username and password, save it and make a retry. 
Finger crossed and if everything going smoothly, you'll see the lovely wonderful output as below.

![Maven build success](/assets/images/maven_proxy_success.png)

# Further reading
There are other Maven errors similiar to this and caused by same rootcause.

### 503 Service Unavailable, proxy: ProxyInfo
```bash
503 Service Unavailable, proxy: ProxyInfo{host='dmy-proxy.prod.abc.com', userName='null', port=8080, type='http', nonProxyHosts='null'} -> [Help 1]
[ERROR] Plugin org.apache.maven.plugins:maven-failsafe-plugin:2.18.1 or one of its dependencies could not be resolved: Failed to read artifact descriptor for org.apache.maven.plugins:maven-failsafe-plugin:jar:2.18.1: Could not transfer artifact org.apache.maven.plugins:maven-failsafe-plugin:pom:2.18.1 from/to central (http://nexus.fx.srv.abc.com/content/groups/public): transfer failed for http://nexus.fx.srv.abc.com/content/groups/public/org/apache/maven/plugins/maven-failsafe-plugin/2.18.1/maven-failsafe-plugin-2.18.1.pom, status: 503 Service Unavailable, proxy: ProxyInfo{host='dmy-proxy.prod.abc.com', userName='null', port=8080, type='http', nonProxyHosts='null'} -> [Help 1]
```
### failed: Connection timed out: connect
```bash
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  01:47 min
[INFO] Finished at: 2021-10-06T14:54:47+11:00
[INFO] ------------------------------------------------------------------------
[ERROR] Failed to execute goal on project notification-service: Could not resolve dependencies for project com.abc.ptt:notification-service:jar:0.0.1-SNAPSHOT: Failed to collect dependencies at com.abc.ptt.messaging:ptt-messaging-common:jar:4.0.0-SNAPSHOT -> com.abc.ptt.messaging:ptt-messagin
g-api:jar:4.0.0-SNAPSHOT: Failed to read artifact descriptor for com.abc.ptt.messaging:ptt-messaging-api:jar:4.0.0-SNAPSHOT: Could not transfer artifact com.abc.ptt.messaging:ptt-messaging-api:pom:4.0.0-SNAPSHOT from/to central (http://nexus.fx.srv.abc.com/content/groups/public): transfer
failed for http://nexus.fx.srv.abc.com/content/groups/public/com/abc/ptt/messaging/ptt-messaging-api/4.0.0-SNAPSHOT/ptt-messaging-api-4.0.0-SNAPSHOT.pom, proxy: ProxyInfo{host='df.proxy.prod.mte.abc.com', userName='null', port=80, type='http', nonProxyHosts='null'}: Connect to df.proxy.
prod.mte.abc.com:80 [df.proxy.prod.mte.abc.com/10.39.66.100] failed: Connection timed out: connect -> [Help 1]
```

--End--


