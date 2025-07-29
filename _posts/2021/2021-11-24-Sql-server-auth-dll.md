---
header:
    image: /assets/images/hd_sql_auth.png
title: SQLServer Error about This driver is not configured for integrated authentication
date: 2021-11-24
tags:
 - SQL Server
 - Java
 - Errors&Solutions
 
permalink: /blogs/tech/en/sqlserver_driver_not_configured_integrated_authenciation
layout: single
---

# Symptoms
When you are using integrated authentication (Kerberos connection) for MS SqlServer connection, there is one possible error :

`This driver is not configured for integrated authentication. ClientConnectionId`

and 

`no mssql-jdbc_auth-9.2.1.x64 in java.library.path:`

 `Failed to load the sqljdbc_auth.dll cause : no sqljdbc_auth in java.library.path`

## Error stack trace
The error strack trace may look like following

```bash
com.microsoft.sqlserver.jdbc.SQLServerException: This driver is not configured for integrated authentication. ClientConnectionId:f965454c-897b-4707-a625-52506e450878
    at com.microsoft.sqlserver.jdbc.SQLServerConnection.terminate(SQLServerConnection.java:3206) ~[mssql-jdbc-9.2.1.jre8.jar:na]
    at com.microsoft.sqlserver.jdbc.AuthenticationJNI.<init>(AuthenticationJNI.java:72) ~[mssql-jdbc-9.2.1.jre8.jar:na]
    at com.microsoft.sqlserver.jdbc.SQLServerConnection.logon(SQLServerConnection.java:4015) ~[mssql-jdbc-9.2.1.jre8.jar:na]



Caused by: java.lang.UnsatisfiedLinkError: no mssql-jdbc_auth-9.2.1.x64 in java.library.path: [C:\soft\java-11-openjdk-11.0.11.9-1.windows.redhat.x86_64\bin, C:\WINDOWS\Sun\Java\bin, C:\WINDOWS\system32, C:\WINDOWS, C:\Python39\Scripts\, C:\Python39\, C:\Program Files (x86)\RSA SecurID Token Common, C:\WINDOWS\system32, C:\WINDOWS, C:\WINDOWS\System32\Wbem, C:\WINDOWS\System32\WindowsPowerShell\v1.0\, C:\WINDOWS\System32\OpenSSH\, C:\Program Files\Git\cmd, c:\dev\scripts\, c:\dev\apache-maven-3.8.1\\bin, C:\Minikube, C:\Soft\nodejs\, C:\ProgramData\chocolatey\bin, C:\Program Files (x86)\Microsoft SQL Server\150\DTS\Binn\, C:\Program Files\Azure Data Studio\bin, C:\Program Files\Docker\Docker\resources\bin, C:\ProgramData\DockerDesktop\version-bin, C:\Program Files\dotnet\, C:\ProgramData\Riverbed\ProcessInjection\rpictrlBin, C:\soft\java\java-11-openjdk-11.0.11.9-1.windows.redhat.x86_64\bin, C:\Program Files (x86)\sbt\bin, C:\Program Files (x86)\scala\bin, C:\Program Files\PowerShell\7\, C:\WINDOWS\system32, C:\WINDOWS, C:\WINDOWS\System32\Wbem, C:\WINDOWS\System32\WindowsPowerShell\v1.0\, C:\WINDOWS\System32\OpenSSH\, C:\Users\XXX\AppData\Local\Microsoft\WindowsApps, C:\soft\JetBrains\IntelliJ IDEA 2021.1.3\bin, ., c:\ProgramData\chocolatey\lib\gradle\tools\gradle-7.2\\bin, C:\soft\Microsoft VS Code\bin, C:\Users\XXX\AppData\Roaming\npm, C:\Program Files\Azure Data Studio\bin, C:\soft\java-11-openjdk-11.0.11.9-1.windows.redhat.x86_64\bin, ., C:\soft\JetBrains\IntelliJ IDEA Educational Edition 2021.2.3\bin, ., C:\soft\JetBrains\IntelliJ IDEA Community Edition 2021.2.3\bin, ., .]
    at java.base/java.lang.ClassLoader.loadLibrary(ClassLoader.java:2670) ~[na:na]
    at java.base/java.lang.Runtime.loadLibrary0(Runtime.java:830) ~[na:na]
    at java.base/java.lang.System.loadLibrary(System.java:1873) ~[na:na]
    at com.microsoft.sqlserver.jdbc.AuthenticationJNI.<clinit>(AuthenticationJNI.java:51) ~[mssql-jdbc-9.2.1.jre8.jar:na]
    at com.microsoft.sqlserver.jdbc.SQLServerConnection.logon(SQLServerConnection.java:4014) ~[mssql-jdbc-9.2.1.jre8.jar:na]
    ... 46 common frames omitted



  2021-11-24 16:11:58.244  WARN 38084 --- [           main] c.m.s.jdbc.internals.AuthenticationJNI   : Failed to load the sqljdbc_auth.dll cause : no sqljdbc_auth in java.library.path: [C:\soft\java-11-openjdk-11.0.11.9-1.windows.redhat.x86_64\bin, C:\WINDOWS\Sun\Java\bin, C:\WINDOWS\system32, C:\WINDOWS, C:\Python39\Scripts\, C:\Python39\, C:\Program Files (x86)\RSA SecurID Token Common, C:\WINDOWS\system32, C:\WINDOWS, C:\WINDOWS\System32\Wbem, C:\WINDOWS\System32\WindowsPowerShell\v1.0\, C:\WINDOWS\System32\OpenSSH\, C:\Program Files\Git\cmd, c:\dev\scripts\, c:\dev\apache-maven-3.8.1\\bin, C:\Minikube, C:\Soft\nodejs\, C:\ProgramData\chocolatey\bin, C:\Program Files (x86)\Microsoft SQL Server\150\DTS\Binn\, C:\Program Files\Azure Data Studio\bin, C:\Program Files\Docker\Docker\resources\bin, C:\ProgramData\DockerDesktop\version-bin, C:\Program Files\dotnet\, C:\ProgramData\Riverbed\ProcessInjection\rpictrlBin, C:\soft\java\java-11-openjdk-11.0.11.9-1.windows.redhat.x86_64\bin, C:\Program Files (x86)\sbt\bin, C:\Program Files (x86)\scala\bin, C:\Program Files\PowerShell\7\, C:\WINDOWS\system32, C:\WINDOWS, C:\WINDOWS\System32\Wbem, C:\WINDOWS\System32\WindowsPowerShell\v1.0\, C:\WINDOWS\System32\OpenSSH\, C:\Users\XXX\AppData\Local\Microsoft\WindowsApps, C:\soft\JetBrains\IntelliJ IDEA 2021.1.3\bin, ., c:\ProgramData\chocolatey\lib\gradle\tools\gradle-7.2\\bin, C:\soft\Microsoft VS Code\bin, C:\Users\XXX\AppData\Roaming\npm, C:\Program Files\Azure Data Studio\bin, C:\soft\java-11-openjdk-11.0.11.9-1.windows.redhat.x86_64\bin, ., C:\soft\JetBrains\IntelliJ IDEA Educational Edition 2021.2.3\bin, ., C:\soft\JetBrains\IntelliJ IDEA Community Edition 2021.2.3\bin, ., .]

```

# Root cause
This is a  hardcode logic in Microsoft JDBC library authentication module.  Downlaoded auth file will be named as mssql-jdbc_auth-9.4.0.x64.dll, it has to renamed to sqljdbc_auth.dll and save to %JAVA_HOME%\bin folder

# Solution
 - Firstly download file from Microsoft folder as below

https://docs.microsoft.com/en-us/sql/connect/jdbc/release-notes-for-the-jdbc-driver?view=sql-server-ver15

 - Then unzip and copy the file under folder "auth"

 - Lastly, copy your platform dill file (e.g. mssql-jdbc_auth-9.4.0.x64.dll) and rename to sqljdbc_auth.dll


![](/assets/images/sql_server_auth.png)


--End--

