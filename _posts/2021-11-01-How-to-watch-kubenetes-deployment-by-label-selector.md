---
title: How to watch specific kubenetes deployment by labels
date: 2021-11-01
tags:
 - Kubenetes
 - K8s
layout: single
category: tech
---

# How to watch specific kubenetes deployment by labels

# Background
You can use Kubenetes Java client library to *watch* any changes in Kubenets, so that you can wire up your hook logic to call business logic upon any changes in K8s. But normally it's waste of resource and time to wathc **all** changes, so youc an apply a filter on specific resouce change by fitlering on Kube *labels*. Here is a mini blog to show how to do so.


# Check which lable to filter on

Here is screnshot from Kubenetes LENS, I'll use label *run=dummy-service* as sample. As highlight in below screenshot.

![](/assets\images\kube_labels.png)

# Sample Java logic

If the label of your deployment in Kubenetse is run=dummy-service, you can use following code logic

```java
 public void run() {
        Watch<V1Deployment> watch = null;
        try {
            watch = Watch.createWatch(
                    client,
                    appsApi.listNamespacedDeploymentCall("YOU_NAME_SPACE", null, null, null, null, "run=dummy-service", null,
                            null, null, null, true, null),
                    new TypeToken<Watch.Response<V1Deployment>>() {
                    }.getType());
        } catch (ApiException e) {
            LOGGER.error("Error occurred in DeploymentWatcher,", e);            
        }
        assert watch != null;
        watch.forEach(this::setMetadata);
    }
```

So above code will return all Deployments with label "run=dummy-service"

# Reference
 - https://appdoc.app/artifact/io.kubernetes/client-java-api/0.1/io/kubernetes/client/apis/AppsV1beta1Api.html#listNamespacedDeploymentCall-java.lang.String-java.lang.String-java.lang.String-java.lang.String-java.lang.String-java.lang.Integer-java.lang.Boolean-io.kubernetes.client.ProgressResponseBody.ProgressListener-io.kubernetes.client.ProgressRequestBody.ProgressRequestListener-

--End--
