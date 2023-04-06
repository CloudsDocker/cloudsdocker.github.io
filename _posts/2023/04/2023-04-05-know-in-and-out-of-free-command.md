---
title: what is StrictHostKeyChecking in ssh
header:
    image: /assets/images/GoogleMap_missing_JPN.jpg
date: 2023-04-06
tags:
- ssh
- devops
- automation

permalink: /blogs/tech/en/what-is-StrictHostKeyChecking-in-ssh
layout: single
category: tech
---

# What's and how to avoid error of the authenticity of host 'xxx' can't be established
You can suppress the "The authenticity of host '' can't be established" message in the SSH command by using the "-o" option with the "StrictHostKeyChecking" parameter set to "no" like this:


```shell
ssh -o StrictHostKeyChecking=no user@hostname
```
This option tells SSH not to check the host key against the known_hosts file and to automatically add the host key to the file without prompting for confirmation. However, it is important to note that this option may compromise the security of your SSH connection, as it allows connections to unknown hosts without verification of their identity.

Alternatively, you can add the host key to the known_hosts file manually before making the connection, which will prevent the message from being displayed in the future. To do this, you can use the ssh-keyscan command to retrieve the host key and add it to the known_hosts file like this:

```shell
ssh-keyscan hostname >> ~/.ssh/known_hosts
```
This command retrieves the host key for the specified hostname and appends it to the end of the known_hosts file in the user's home directory.

--HTH--
