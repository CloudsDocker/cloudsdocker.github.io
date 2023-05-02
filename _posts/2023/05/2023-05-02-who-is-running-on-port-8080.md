---
title: who-is-running-on-port-8080
header:
    image: /assets/images/let-AI-to-manage-stripe-payment.jpg
date: 2023-05-02
tags:
- AI
- stripe
- automation

permalink: /blogs/tech/en/let-AI-to-manage-stripe-payment
layout: single
category: tech
---
> A young idler, an old beggar. - William Shakespeare

## How to find process running on port 8080 and kill it in Windows 10

1. find the process on 8080

```
netstat -ano | findstr 8080
```

2. locate the process id:


```
 TCP    0.0.0.0:8080           0.0.0.0:0              LISTENING       33584
 TCP    [::]:8080              [::]:0                 LISTENING       33584
```


3. Kill the process by PID

```
taskkill /F /PID 33584
```


Thank you for reading, and happy coding!


--HTH--
