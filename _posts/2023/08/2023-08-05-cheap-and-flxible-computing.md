---
title: Cheap and flexible computing
header:
    image: /assets/images/Cheap_and_flexible_computing.jpg
date: 2023-08-05
tags:
- CloudComputing
- AWS
- Fargate
- ECS

permalink: /blogs/tech/en/Cheap_and_flexible_computing
layout: single
category: tech
---
> whether it seems possible or not - go for it
> 
# Cheaper X 2 to EC2, to use Fargate Spot
With Fargate Spot you can run interruption tolerant Amazon ECS tasks at a discounted rate compared to
the AWS Fargate price. Fargate Spot runs tasks on spare compute capacity. When AWS needs the capacity
back, your tasks will be interrupted with a two-minute warning.

# To fast loading docker image
With SOCI, containers only spend a few seconds on the image pull before
they can start, providing time for environment setup and application instantiation while the image is
downloaded in the background. This is called lazy loading. When Fargate starts an Amazon ECS task,
Fargate automatically detects if a SOCI index exists for an image in the task and starts the container
without waiting for the entire image to be downloaded.
For containers that run without SOCI indexes, container images are downloaded completely before
the container is started. This behavior is the same on all other platform versions of Fargate and on the
Amazon ECS-optimized AMI on Amazon EC2 instances

We recommend that you try lazy loading with container images greater than 250 MiB in size. You are
less likely to see a reduction in the time to load smaller images.


HTH