---
title: docker-commands-bible
header:
    image: /assets/images/docker-commands-bible.jpg
date: 2023-05-22
tags:
- Docker
- Programming
- Container

permalink: /blogs/tech/en/docker-commands-bible
layout: single
category: tech
---
> "Don't let yesterday take up too much of today." - Will Rogers



# Displaying Full Command Line of Docker Containers with `docker ps`

When working with Docker containers, you might often want to view the full command line of running containers. By default, the `docker ps` command provides a truncated version of the command line. However, there is a simple option that allows you to display the complete command line: `--no-trunc`.

## Using the `--no-trunc` Option

To show the full command line of Docker containers, follow these steps:

1. Open a terminal or command prompt.

2. Run the following command:

```shell
sudo docker ps --no-trunc
```

The `docker ps` command is used to list running containers, and the `--no-trunc` option ensures that the full command line is displayed without truncation.

3. The output will now include the complete command line for each running container, allowing you to see the full details.

That's it! With the `--no-trunc` option, you can easily view the full command line of Docker containers and gain more insight into the running processes.

## Conclusion

Displaying the full command line of Docker containers using the `docker ps` command is a useful technique when you need to examine the exact command that launched a container. By including the `--no-trunc` option, you can ensure that the complete command line is shown without any truncation.

Being able to view the full command line can help you troubleshoot issues, understand how a container is configured, and gain better visibility into the running processes.

Next time you need to inspect the command line of a Docker container, remember to use the `--no-trunc` option with the `docker ps` command, and you'll have access to the complete details.

Happy containerizing!

---


--HTH--
