---
layout: posts
title: Microservices vs. SOA
tags: 
 - Microservices
 - SOA
---

# Microservice
- Services are organized around capabilities, e.g., user interface front-end, recommendation, logistics, billing, etc.
- Services are small in size, messaging enabled, bounded by contexts, autonomously developed, independently deployable, decentralized and built and released with automated processes.
- resource-oriented computing (ROC) as a generalized form of the Web abstraction. If in the Unix abstraction "everything is a file", in ROC, everything is a "Micro-Web-Service"

## Philosophy

The philosophy of the microservices architecture essentially equates to the Unix philosophy of "Do one thing and do it well". It is described as follows:

- The services are small - fine-grained to perform a single function.
- The organization culture must embrace automation of testing and deployment. This eases the burden on management and operations and allows for different development teams to work on independently deployable units of code.
- The culture and design principles must embrace failure and faults, similar to anti-fragile systems.
- Each service is elastic, resilient, composable, minimal, and complete.

## service mesh
In a service mesh, each service instance is paired with an instance of a reverse proxy server, called a service proxy, sidecar proxy, or sidecar. The service instance and sidecar proxy share a container, and the containers are managed by a container orchestration tool such as Kubernetes.



# Differences between Microservices and SOA

## Definitaion of SOA

- `Boundaries` are explicit
- Services are `autonomous`
- Services share __ schema __ and **contract**, not class
- Service compatibility is based on policy

---

> In short, the microservice architectural style is an approach to developing a single application as a suite of small services, each running in its own process and communicating with lightweight mechanisms, often an HTTP resource API. These services are built around business capabilities and independently deployable by fully automated deployment machinery. There is a bare mininum of centralized management of these services, which may be written in different programming languages and use different data storage technologies.




### Related links:

- [InfoQ Discussions](https://www.infoq.com/news/2015/12/soa-v-microservices)
- [StackOverFlow](http://stackoverflow.com/questions/25501098/difference-between-microservices-architecture-and-soa)
- [Microservices tag desc](http://stackoverflow.com/tags/microservices/info)
- [MartinFowler](http://martinfowler.com/articles/microservices.html)
