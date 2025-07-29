---
title: Container
tags:
- DevOps
layout: posts
---

The Docker project was responsible for popularizing container development in Linux systems. The original project defined a command and service (both named docker) and a format in which containers are structured. This chapter provides a hands-on approach to using the docker command and service to begin working with containers in Red Hat Enterprise Linux 7 and RHEL Atomic Host by getting and using container images and working with running containers. 


 Containers provide a means of packaging applications in lightweight, portable entities. Running applications within containers offers the following advantages:

- **Smaller than Virtual Machines**: Because container images include only the content needed to run an application, saving and sharing is much more efficient with containers than it is with virtual machines (which include entire operating systems)
- **Improved performance**: Likewise, since you are not running an entirely separate operating system, a container will typically run faster than an application that carries with it the overhead of a whole new virtual machine.
- **Secure**: Because a container typically has its own network interfaces, file system, and memory, the application running in that container can be isolated and secured from other activities on a host computer.
- **Flexible**: With an application’s run time requirements included with the application in the container, a container is capable of being run in multiple environments. 



RHEL Atomic Host is a light-weight Linux operating system distribution that was designed specifically for running containers. It contains two different versions of the docker service, as well as some services that can be used to orchestrate and manage Docker containers, such as Kubernetes. Only one version of the docker service can be running at a time. 


# Images

Containers in OpenShift Origin are based on Docker-formatted container images. An image is a binary that includes all of the requirements for running a single container, as well as metadata describing its needs and capabilities.


You can think of it as a packaging technology. Containers only have access to resources defined in the image unless you give the container additional access when creating it. By deploying the same image in multiple containers across multiple hosts and load balancing between them, OpenShift Origin can provide redundancy and horizontal scaling for a service packaged into an image.

## Container Registries
A container registry is a service for storing and retrieving Docker-formatted container images. A registry contains a collection of one or more image repositories. Each image repository contains one or more tagged images. Docker provides its own registry, the Docker Hub, and you can also use private or third-party registries. Red Hat provides a registry at registry.access.redhat.com for subscribers. OpenShift Origin can also supply its own internal registry for managing custom container images.



# Reference 
 -  https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_atomic_host/7/single/getting_started_with_containers/index#introduction_to_linux_containers
