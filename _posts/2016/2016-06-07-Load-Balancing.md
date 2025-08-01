---
layout: posts
title: Load Balancing
tags:
 - CTO
 - MobileInternet
 - DevOps
---

# Concepts
`LVS` means Linux Virtual Server, which is one Linux built-in component. 

# Some logics of LVS

## Never Queue Shceduling
> The never queue scheduling algorithm adpots a two-speed model

1. When there is an idel server avaiable, the job will be sent to the idel server, instead of waiting for a fast one.
1. When there is no idel server avaiable, the job will be sent to the server that minimize it's expected delay.


# Examples 

## Setup LVS
```sh
ipvsadm -A -t 192.168.0.1:80 -s rr
ipvsadm -a -t 192.168.0.1:80 -r 172.16.0.1:80 -m
ipvsadm -a -t 192.168.0.1:80 -r 172.16.0.2:80 -m
```
- The first command assign TCP port 80 on IP address 192.168.0.1 to the virtual server, the shceduling algorithm for load balancing is `-s rr` means using round-robin
- The 2nd and 3rd commands are adding IP addresss of `real servers` to the LVS setup
- the forwarded network packets shall be masked `-m`

## To query LVS status
```sh
ipvsadm -L -n
IP Virtual Server version 1.0.8 (size=65536)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  192.168.0.1:80 rr
  -> 172.16.0.2:80                Masq    1      3          1
  -> 172.16.0.1:80                Masq    1      4          0
```

## Strucutre of LVS in wikipedia
![Strucutre of LVS in wikipedia](https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Wikimedia_Server_Architecture_%28simplified%29.svg/743px-Wikimedia_Server_Architecture_%28simplified%29.svg.png)
