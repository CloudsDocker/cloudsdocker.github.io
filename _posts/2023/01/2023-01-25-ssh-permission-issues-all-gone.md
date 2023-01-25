---
header:
    image: /assets/images/hd_magic_micronaut_jpa.jpg
title:  One killer page to fix most permission issues when using SSH
date: 2023-01-25
tags:
 - ssh
 
permalink: /blogs/tech/en/ssh_permission_issues_all_gone
layout: single
category: tech
---

> The best way to predict the future is to create it.

# You are required to enter password even on correct private key
## Symptoms
If you are sure correct ssh PSK keys installed in your `~/.ssh/` , but keep on requesting enter password when login, it worked fine and ssh connection got established after you enter password. That's annoying to have to enter password every time even connection is good after enter password.

```shell
debug1: send_pubkey_test: no mutual signature algorithm
debug1: Offering public key: /Users/todd.zhang/.ssh/id_rsa_xxx RSA SHA256:XXXXXXXX73dP1XpAw8H2nRPBPWrA3o0 explicit
debug1: send_pubkey_test: no mutual signature algorithm
debug1: Next authentication method: password
your.username@jumpserver-abc.com's password:
```
## Solution
- open file ~/.ssh/config
- Add following line (PubkeyAcceptedKeyTypes +ssh-rsa) into the block for this ssh connection session 

```shell
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_rsa_xxx
  PubkeyAcceptedKeyTypes +ssh-rsa
```

--HTH--



