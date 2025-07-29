---
title: Openshift tips
tags:
- cloud
- DevOps
layout: posts
---

# Commands bible

## install cli in Mac
```sh
brew install openshift-cli
```

## Frequently used commands

### Start mini shift
```sh
minishift start
```

### OC commands
```sh
oc config view
```

#### Start a new application
```sh
oc new-app https://github.com/openshift/nodejs-ex -l name=toddapp
```

#### To switch project
```sh
oc project 
```

#### Show a high level overview of the current project 
```sh
oc status
# Export the overview of the current project in an svg file.
  oc status -o dot | dot -T svg -o project.svg
  
  # See an overview of the current project including details for any identified issues.
  oc status -v
```

This command will show services, deployment configs, build configurations, and active deployments.
If you have any misconfigured components information about them will be shown. For more information
about individual items, use the describe command (e.g. oc describe buildConfig, oc describe
deploymentConfig, oc describe service). 

You can specify an output format of "-o dot" to have this command output the generated status graph
in DOT format that is suitable for use by the "dot" command.


## OpenShift command-line tool
The OpenShift command-line tool oc is the primary way most users interact with OpenShift. The command-line tool talks via a REST API exposed by the OpenShift cluster. 

## Pod
The most basic unit in OpenShift are pods. A pod is one or more containers guaranteed to be running on the same host. The containers within a pod share a unique IP address. They can communicate with each other via the “localhost” and also all share any volumes (persistent storage). The containers themselves are started from an image, which in our case is a Docker image.    

OpenShift Origin leverages the Kubernetes concept of a pod, which is one or more containers deployed together on one host, and the smallest compute unit that can be defined, deployed, and managed.

Pods are the rough equivalent of a machine instance (physical or virtual) to a container. Each pod is allocated its own internal IP address, therefore owning its entire port space, and containers within pods can share their local storage and networking.

Pods have a lifecycle; they are defined, then they are assigned to run on a node, then they run until their container(s) exit or they are removed for some other reason. Pods, depending on policy and exit code, may be removed after exiting, or may be retained in order to enable access to the logs of their containers.

Pods have a lifecycle; they are defined, then they are assigned to run on a node, then they run until their container(s) exit or they are removed for some other reason. Pods, depending on policy and exit code, may be removed after exiting, or may be retained in order to enable access to the logs of their containers.

OpenShift Origin treats pods as largely immutable; changes cannot be made to a pod definition while it is running. OpenShift Origin implements changes by terminating an existing pod and recreating it with modified configuration, base image(s), or both. Pods are also treated as expendable, and do not maintain state when recreated. Therefore pods should usually be managed by higher-level controllers, rather than directly by users.


## Scale up
When scaled up, an application will have more than one copy of itself, and each copy will have its own local state. Each copy corresponds to a different instance of a pod with the pods being managed by the replication controller. As each pod has a unique IP, we need an easy way to address the set of all pods as a whole. This is where a service comes into play. The service gets its own IP and a DNS name. When making a connection to a service, OpenShift will automatically route the connection to one of the pods associated with that service.

caling from the Web Console
Scaling up the number of instances of your application running can be done from the Overview page for your application in the OpenShift web console (the page with those tell-tale up and down arrows we saw previously). Jump to that page and click the up arrow key twice to increase the replica count to 3
If your application is a web application that adheres to the 12-factor methodology, or what might also be called a cloud native application, then it would generally be safe to scale up.

Applications that can’t usually be able to be scaled up include traditional relational databases backed by persistent storage. Databases cannot be scaled in the traditional way as only the primary instance of the database should have the ability to update data. Scaling can still be performed, but usually only on read-only instances of the database.

## Kubernetes and Openshift
The basic concepts of Kubernetes and discuss how OpenShift builds on them. In general, you can view Kubernetes as being aimed at Ops teams, providing them with a tool for running containers at scale in production. OpenShift adds to this by also supporting the work of a Dev team and others by making the job of the Ops team easier, which helps to bridge the gap between Dev and Ops and thus enable the latest DevOps philosophy.OpenShift provides a number of different ways to interact with an OpenShift cluster. The OpenShift command-line tool oc is the primary way most users interact with OpenShift. The command-line tool talks via a REST API exposed by the OpenShift cluster. 
If you want to avoid using the command line tool, or you want to automate your interactions with the OpenShift cluster, you can always use the REST API directly.

You may be wondering: “Is a namespace the same thing as an application?” OpenShift has no formal concept of an application, thereby allowing an application to be flexible depending on a user’s needs.

You can dedicate one to everything related to just one application. Or, so long as you label all the resources making up an application so you know what goes with what, you can also use the namespace to hold more than one.

# Secrets

This topic discusses important properties of secrets and provides an overview on how developers can use them.

The Secret object type provides a mechanism to hold sensitive information such as passwords, OpenShift Origin client configuration files, dockercfg files, private source repository credentials, and so on. Secrets decouple sensitive content from the pods. You can mount secrets into containers using a volume plug-in or the system can use secrets to perform actions on behalf of a pod.



## Route
Although a service has a DNS name, it is still only accessible within the OpenShift cluster and is not accessible externally. To make a service externally accessible, a route needs to be created. Creating a route automatically sets up haproxy or a hardware-based router, with an externally addressable DNS name, exposing the service and load-balancing inbound traffic across the pods.

## image
The output of the build process is an image, which is stored in an integrated Docker registry ready for distribution out to nodes when the application is deployed. The image stream is how the image and its versions are tracked by OpenShift. If you already have an existing Docker image on an external registry such as Docker Hub, it can also be referenced by an image stream instead of building it locally.

use the handy online cheat sheet available by running the oc types command. It gives you a quick summary of the different conceptual types and definitions used in OpenShift like those we covered here:


## Vagrant
Vagrant is a software tool that allows users to create and configure lightweight, reproducible, and portable development environments. It works in conjunction with virtualization (both VMs and IaaS) to automate all the steps necessary to get your dev environment going



One of the advantages of creating and deploying applications from the web console is that a route is automatically created for you. When deploying new containers while using the oc tool, you will need to expose the service manually

## Volumes

One of the great features of the OpenShift platform is the ability to provide persistent volumes for your running pods. This ensures that data in your database doesn’t suddenly disappear if the container is restarted. Another important aspect of persistent volumes is the ability to run both stateful and stateless applications on the platform. This is sometimes referred to as mode 1 and mode 2 applications as well as legacy and 12-factor applications.

## webhooks
Automatic Deployments Using Webhooks
A webhook (also called a web callback or HTTP push API) is a way an application can provide other applications with real-time information or notifications.

We can configure the GitHub code hosting service to trigger a webhook each time we push a set of changes to your project code repository. Using this tool, we can notify OpenShift when you have made code changes and thus initiate rebuild and redeployment of our application.


## Deployment Strategies
A deployment strategy defines the process by which a new version of your application is started and the existing instances shut down. By default OpenShift uses a rolling deployment strategy that enables you to perform an update with no apparent down time.
