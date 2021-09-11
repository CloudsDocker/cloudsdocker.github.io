---
layout: posts
title: Docker Errors and Fixes
tags:
 - DevOps
 - Docker
---

# Docker Errors

1. Cannot connect to the Docker daemon. Is the docker daemon running on this host?
The solution is to run under root user, e.g. 

```sh
sudo docker run hello-world
```

1. Docker service

```sh
 sudo service docker status
 sudo service docker start
 sudo docker run hello-world
```

