---
title: TypeScript noteworthy notes
tags:
- Angular
- JavaScript
layout: posts
---
# Async Await keywords
Async Await Support in TypeScript
Async - Await has been supported by TypeScript since version 1.7. Asynchronous functions are prefixed with the async keyword; await suspends the execution until an asynchronous function return promise is fulfilled and unwraps the value from the Promise returned. It was only supported for target es6 transpiling directly to ES6 generators.



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
