---
title: TypeScript noteworthy notes
---

# Troubleshotting

## Unexpected token ...

That's because your node version is lower (e.g. node v4.x), which don't support spread operator. You'd firstly check your node version 
```bash
node -v
```

If above result say node is v4.x, then you should run following commands to upgrade your node. Normally you can leverage Node Package Manager `n` as below:
```shell
sudo npm install -g n
sudo n stable 
```