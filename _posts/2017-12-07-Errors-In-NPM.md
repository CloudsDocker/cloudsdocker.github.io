---
title: common errors in NPM or node
tags:
- nodejs
- javascript
- anugar
layout: posts
---

## code E503
code E503 when run npm install packages, e.g.

```sh
npm install pretty-data
```
Get following error:
`
npm ERR! code E503
npm ERR! 503 Service Unavailable: pretty-data@latest

npm ERR! A complete log of this run can be found in:
npm ERR!     xxxx\nodejs\npm-cache\_logs\2017-12-07T04_16_53_679Z-debug.log

### Solution:
You maybe behind corporate proxy, so try execute following command 
```sh
npm config set proxy http://127.0.0.1:53128
```
