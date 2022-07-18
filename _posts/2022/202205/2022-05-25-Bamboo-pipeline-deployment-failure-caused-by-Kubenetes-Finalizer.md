---
header:
    image: /assets/images/hd_kubenetes_bamboo_deployment.png
title:  Bamboo pipeline deployment failure caused by Kubenetes Finalizer
date: 2022-05-25
tags:
 - bamboo
 - CI/CD
 - DevOps
 - K8s
 - Kubernetes
 - Helm 
permalink: /blogs/tech/en/Bamboo-pipeline-deployment-failure-caused-by-Kubenetes-Finalizer
layout: single
category: tech
---

> Today a reader, tomorrow a leader.

# Summary
In current CI/CD world, for DevOps tasks,  many teams chose to use Bamboo API/Library running together with `HELM chart` and `Kubernetes`, to run actual deployemnt in Bamboo pipeline.  You may get following weird error .

```bash

build	25-May-2022 16:34:02	### HELM Deploy - my-awesome-micro-service
build	25-May-2022 16:34:02	
build	25-May-2022 16:34:02	Release "my-awesome-micro-service" does not exist. Installing it now.
error	25-May-2022 16:34:03	Error: rendered manifests contain a resource that already exists. Unable to continue with install: existing resource conflict: namespace: myspace, name: my-awesome-micro-service, existing_kind: apps/v1, Kind=Deployment, new_kind: apps/v1, Kind=Deployment
build	25-May-2022 16:34:03	
build	25-May-2022 16:34:03	### HELM chart history
build	25-May-2022 16:34:03	
error	25-May-2022 16:34:04	Error: release: not found
build	25-May-2022 16:34:04	
build	25-May-2022 16:34:04	Helm Deploy FAILED
```

# Error details & solutions

From the log description, it's kind of a paradox, it claiming `my-awesome-micro-service` not exist, so trying to install it. At the meanwhile, it encounter one error saying this service already exist, so failed to install it. 

The root cause is **previous deployment** failed to delete, so installing **new version** not work. 

This is actually caused by *finalizer* in Kubenetes. If you check the service in **LENS** for this service's deployment, you'll find it.

![](/assets/images/kubenetes_bamboo_deployment_error.png)

The solution is simple, just delete this *finalizer*, you can run this via following command. 

```bash
kubectl -n pretrade patch deployment/my-awesome-micro-service -p '{"metadata":{"finalizers":null}}'
```



--HTH--



