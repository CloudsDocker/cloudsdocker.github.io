---
title: Deep dive into Kubernetes Client API
date: 2021-09-16
tags:
 - Kubernetes
 - K8s
layout: single
---

# Summary
To talk to K8s for getting data, there are few approaches. While K8s' official Java library is the most widely used one.
This blog will look into this client library.


# ClientAPI
This class is essentially a wraper of library `OKHttp`, which will call K8s Restful API to get data back.

To have a new client API, you can either using username/password, CA token or in-cluster client API.

## In-clust client API
This is means your appilcatin is runing inside Kubernetes, so that it will read various configrations from running environment. This will save lots time to setup tokens, login details.

Here is one sample FYI.
https://github.com/kubernetes-client/java/blob/master/examples/examples-release-12/src/main/java/io/kubernetes/client/examples/InClusterClientExample.java

Firstly, call follwoing command
ClientBuilder.cluster

Creates a builder which is pre-configured from the cluster configuration. Following details will be loaded from running envrionemnt :
  - KUBERNETES_SERVICE_HOST 
  - KUBERNETES_SERVICE_PORT
  - SERVICEACCOUNT_CA_PATH (/var/run/secrets/kubernetes.io/serviceaccount/ca.crt)
  - SERVICEACCOUNT_TOKEN_PATH (/var/run/secrets/kubernetes.io/serviceaccount/token)


For accesstoken,

    
    
    builder.setAuthentication(new TokenFileAuthentication(SERVICEACCOUNT_TOKEN_PATH)); //cluster
    vs
    builder.setAuthentication(new AccessTokenAuthentication(token)); // oldCluster


In windows operation system, if you want to get your CPU name, core, 64bit and speed in command line. Just follow below actions:

   1. Press `Win+R` and type *cmd*
   1. Enter following command to get your CPU details.

```bash
wmic cpu get caption, deviceid,name, numberofcores,maxclockspeed,status
```
You'll get output simliar to below:

![](/assets/images/ShowCPUsInWin.png)

```bash
Caption                               DeviceID  MaxClockSpeed  Name                                NumberOfCores  Status

Intel64 Family 6 Model 85 Stepping 7  CPU0      3912           Intel(R) Xeon(R) W-2245 CPU @ 3.90GHz  8              OK
```

Addtionally reading, this `wmic` is an utility shipped by Windows OS. It's full name is WMI command-line (WMIC) , one utility provides a command-line interface for Windows Management Instrumentation (WMI).


--End--
