---
header:
    image: /assets/images/yarn_npm_install.jpg
title: Kubenetes Zero to Hero
date: 2024-09-27
tags:
 - Kubernetes
 - DevOps
 - Platform

permalink: /blogs/tech/en/kubenetes-zero-to-hero
layout: single
category: tech
---

> You are not a drop in the ocean, you are the entire ocean in a drop.

# Services

There are two major categories of services in Kubernetes:
 - NodePort
 - LoadBalancer



# Services Types

- Stateful Services
- Stateless Services

Stateful Services are those that have a persistent identity. They are usually used for databases, caches, and other stateful applications. Stateless Services, on the other hand, are those that do not have a persistent identity and are used for tasks such as web servers, APIs, and message queues.

# Deployments

A Deployment is a Kubernetes resource that manages the deployment and scaling of a ReplicaSet. It ensures that the desired number of replicas are running at all times.

# ReplicaSet

A ReplicaSet is a Kubernetes resource that manages the deployment and scaling of a set of Pods. It ensures that the desired number of replicas are running at all times.

# Pods

A Pod is a Kubernetes resource that represents a single instance of a running process in a cluster. It is the smallest and simplest unit in the Kubernetes object model.

# Containers

A Container is a lightweight, stand-alone, executable package of software that includes everything needed to run an application: code, runtime, system tools, system libraries, and settings.

# Kubernetes Architecture

Kubernetes is a container orchestration platform that automates the deployment, scaling, and management of containerized applications. It provides a way to run containers in a cluster, manage the cluster, and ensure the containers are running in a reliable and efficient manner.

The Kubernetes architecture consists of several components, including:

- Master Nodes
- Worker Nodes
- Container Runtime
- Container Networking
- Container Orchestration

Master Nodes are responsible for managing the cluster and ensuring that all the necessary components are running on the cluster. Worker Nodes are responsible for running the containers and providing the necessary resources to the containers.

Container Runtime is responsible for running the containers and providing the necessary resources to the containers. Container Networking is responsible for managing the networking between the containers and the outside world. Container Orchestration is responsible for managing the containers and ensuring that they are running in a reliable and efficient manner.

# Kubernetes Components

Kubernetes has several components that work together to provide the necessary functionality for managing the cluster and running the containers. These components include:

- Kubernetes Master
- Kubernetes Worker
- Kubernetes API Server
- Kubernetes Controller Manager
- Kubernetes Scheduler
- Kubernetes Kubelet

The Kubernetes Master is responsible for managing the cluster and ensuring that all the necessary components are running on the cluster. The Kubernetes Worker is responsible for running the containers and providing the necessary resources to the containers. The Kubernetes API Server is responsible for managing the APIs and providing the necessary functionality to the clients. The Kubernetes Controller Manager is responsible for managing the controllers and ensuring that they are running in a reliable and efficient manner. The Kubernetes Scheduler is responsible for scheduling the containers and ensuring that they are running in a reliable and efficient manner. The Kubernetes Kubelet is responsible for running the containers and providing the necessary resources to the containers.

# Kubernetes Architecture Diagram

![Kubernetes Architecture Diagram](/assets/images/kubernetes-architecture-diagram.png)

# Kubernetes Architecture Diagram Explained

The Kubernetes Architecture Diagram is a visual representation of the different components and their interactions in a Kubernetes cluster. It shows the different components of the Kubernetes architecture, their responsibilities, and how they interact with each other.

The diagram consists of several layers, including:

- Node Layer
- Control Plane Layer
- Data Plane Layer

The Node Layer represents the worker nodes in the cluster. It shows the different components of the Kubernetes architecture that are responsible for running the containers and providing the necessary resources to the containers.

The Control Plane Layer represents the master nodes in the cluster. It shows the different components of the Kubernetes architecture that are responsible for managing the cluster and ensuring that all the necessary components are running on the cluster.

The Data Plane Layer represents the components that are responsible for managing the APIs and providing the necessary functionality to the clients. It shows the different components of the Kubernetes architecture that are responsible for managing the APIs and providing the necessary functionality to the clients.
LoadBalancer
