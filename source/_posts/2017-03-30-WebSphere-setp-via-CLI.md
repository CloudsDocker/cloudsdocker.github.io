---
layout: page
title: Setup WebSphere profiles and application in command line
tags:
- WAS
- WebSphere
---

# Setup WebSphere profiles and application in command line

## Noteworthy points
- Please be advised  
### Tools/utilities 
- create profile
```sh
/opt/IBM/WebSphere85/AppServer/bin/manageprofiles.sh
```
- check server status
```sh
/opt/IBM/WebSphere85/AppServer/bin/serverStatus.sh -all
```

- start server 
```sh
/opt/IBM/WebSphere85/AppServer/bin/startServer.sh SERVER_NAME
```

- start server 
```sh
/opt/IBM/WebSphere85/AppServer/bin/stopServer.sh dmgr
```

- deploy application 
```sh
sudo -u wasadm /opt/IBM/WebSphere85/utilities/API/v1.0/AppMgmt -deploy -deployMechanism simpleDeploy -appId xxx_war -appEnvId xxx -file "/tmp/xxx.ear"
```

- stop&start application 
```sh
sudo -u wasadm /opt/IBM/WebSphere85/utilities/API/v1.0/AppMgmt -operate -appId xxx_war -appEnvId xxx -stop
sudo -u wasadm /opt/IBM/WebSphere85/utilities/API/v1.0/AppMgmt -operate -appId xxx_war -appEnvId xxx -start
```



## To create profile
```sh 
sudo -u wasadm /opt/IBM/WebSphere85/AppServer/bin/manageprofiles.sh -create -profileName TEST_PROFILE -profilePath /opt/IBM/WebSphere85/AppServer/profiles/appprofiles/TEST_PROFILE -templatePath /opt/IBM/WebSphere85/AppServer/profileTemplates/default -serverName testSrv01 -nodeName testNode01 -hostName testserver.com -enableAdminSecurity true -adminUserName wasadmin -adminPassword wasadmin@12
```


 
## Errors & troubleshooting

### Server can't started after profile creation
- You may find following errors if you try to bring up server after profile created
```sh
sudo -u wasadm /opt/IBM/WebSphere85/AppServer/bin/startServer.sh TEST_PROFILE
ADMU0116I: Tool information is being logged in file
           /opt/IBM/WebSphere85/AppServer/profiles/dmgrprofile/logs/TEST_PROFILE/startServer.log
ADMU0128I: Starting tool with the dmgrprofile profile
ADMU3100I: Reading configuration for server: TEST_PROFILE
ADMU0111E: Program exiting with error: java.io.FileNotFoundException:
           /opt/IBM/WebSphere85/AppServer/profiles/dmgrprofile/config/cells/wascell/nodes/dmgrnode/servers/TEST_PROFILE/server.xml
```

#### Solution:
- Please use the server name, rather than the profile name , e.g. should be testSrv01, rather than TEST_PROFILE
- The command should be:
```sh
sudo -u wasadm /opt/IBM/WebSphere85/AppServer/bin/startServer.sh testSrv01
```
- On the other hand, you can troubleshoot this issue by double checking the server.xml by 
```sh
ll /opt/IBM/WebSphere85/AppServer/profiles/appprofiles/TEST_PROFILE/config/cells/xxxxx/nodes/testNode01/servers/testSrv01/server.xml
```

### WebServer console can't opened
- There are few reasones, such as:
#### DNS errors 
- If the error as below:
This webpage is not available
The server at testserver.com can't be found, because the DNS lookup failed. DNS is the network service that translates a website's name to its Internet address.
##### Solutions:
That's maybe something wrong for DNS as stated above, so please try to either udpate hosts file in you workstation or repalce the URL by IP address, e.g. 
replace https://testserver.com:9045/ibm/console/login.do?action=secure with https://123.123.112.123:9045/ibm/console/login.do?action=secure

#### What's the port number for WAS console
##### You should get to know it after profile created
For example, in aforesaid profile creation step, you'll get following in output:
```sh
INSTCONFSUCCESS: Success: Profile TEST_PROFILE now exists. Please consult /opt/IBM/WebSphere85/AppServer/profiles/TEST_PROFILE/logs/AboutThisProfile.txt for more information about this profile.
```
To check content of this file, you'll find following snipets:
```sh
Administrative console port: 9060
Administrative console secure port: 9043
```
##### Check the port number from serverindex.xml
```sh
grep -a2 WC_adminhost /opt/IBM/WebSphere85/AppServer/profiles/appprofiles/TEST_PROFILE/config/cells/xxxx/nodes/testNode01/serverindex.xml
```
You'll find the port number listed as below:
```xml
 <endPoint xmi:id="EndPoint_1183122129645" host="testserver.com" port="9407"/>
    </specialEndpoints>
    <specialEndpoints xmi:id="NamedEndPoint_1183122129646" endPointName="WC_adminhost">
      <endPoint xmi:id="EndPoint_1183122129646" host="*" port="9062"/>
    </specialEndpoints>
--
      <endPoint xmi:id="EndPoint_1183122129648" host="*" port="9355"/>
    </specialEndpoints>
    <specialEndpoints xmi:id="NamedEndPoint_1183122129649" endPointName="WC_adminhost_secure">
      <endPoint xmi:id="EndPoint_1183122129649" host="*" port="9045"/>
    </specialEndpoints>
```

##### Check networking & port on WAS server

```sh 
root@cn000tst1129 Thu Mar 30 17:07:11 /  #netstat -nptlev | grep java
tcp        0      0 133.14.16.2:20962           0.0.0.0:*                   LISTEN      200000000  938007     252552/java
tcp        0      0 127.0.0.1:9635              0.0.0.0:*                   LISTEN      200000000  1048485    254902/java
tcp        0      0 0.0.0.0:9445                0.0.0.0:*                   LISTEN      200000000  1048615    254902/java
tcp        0      0 0.0.0.0:9062                0.0.0.0:*                   LISTEN      200000000  1048613    254902/java
tcp        0      0 0.0.0.0:9102                0.0.0.0:*                   LISTEN      200000000  1048479    254902/java
tcp        0      0 0.0.0.0:8882                0.0.0.0:*                   LISTEN      200000000  1048484    254902/java
tcp        0      0 0.0.0.0:9045                0.0.0.0:*                   LISTEN      200000000  1048616    254902/java
tcp        0      0 0.0.0.0:20950               0.0.0.0:*                   LISTEN      200000000  938036     252552/java
tcp        0      0 0.0.0.0:20953               0.0.0.0:*                   LISTEN      200000000  937999     252552/java
tcp        0      0 0.0.0.0:9082                0.0.0.0:*                   LISTEN      200000000  1048614    254902/java
tcp        0      0 0.0.0.0:20954               0.0.0.0:*                   LISTEN      200000000  938118     252552/java
tcp        0      0 0.0.0.0:2811                0.0.0.0:*                   LISTEN      200000000  1048482    254902/java
tcp        0      0 0.0.0.0:20957               0.0.0.0:*                   LISTEN      200000000  937992     252552/java
tcp        0      0 0.0.0.0:9407                0.0.0.0:*                   LISTEN      200000000  1048481    254902/java
tcp        0      0 0.0.0.0:20959               0.0.0.0:*                   LISTEN      200000000  938088     252552/java
tcp        0      0 0.0.0.0:9408                0.0.0.0:*                   LISTEN      200000000  1048480    254902/java
tcp        0      0 127.0.0.1:20960             0.0.0.0:*                   LISTEN      200000000  938089     252552/java
tcp        0      0 133.14.16.2:20961           0.0.0.0:*                   LISTEN      200000000  938047     252552/java
```
