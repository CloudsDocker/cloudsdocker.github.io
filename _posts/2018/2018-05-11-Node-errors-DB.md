---
header:
    image: /assets/images/hd_nodejs_faq.png
date: 2022-03-09
title: Solution center for Node errors 
tags:
- troubleshooting
- NodeJs
- Angular
layout: single
category: tech
permalink: /blogs/tech/en/nodejs_faq_solutions
---
> Fina a way. If there's none, make one!

# Errors list
## Error : Cannot find module 'semver'

### Sympthoms
```bash
node:internal/modules/cjs/loader:933
  const err = new Error(message);
              ^

Error: Cannot find module 'semver'
Require stack:
- C:\soft\nodejs\node_modules\npm\lib\utils\unsupported.js
- C:\soft\nodejs\node_modules\npm\lib\cli.js
- C:\soft\nodejs\node_modules\npm\bin\npm-cli.js
    at Function.Module._resolveFilename (node:internal/modules/cjs/loader:933:15)
    at Function.Module._load (node:internal/modules/cjs/loader:778:27)
    at Module.require (node:internal/modules/cjs/loader:1005:19)
    at require (node:internal/modules/cjs/helpers:102:18)
    at Object.<anonymous> (C:\soft\nodejs\node_modules\npm\lib\utils\unsupported.js:2:16)
    at Module._compile (node:internal/modules/cjs/loader:1103:14)
    at Object.Module._extensions..js (node:internal/modules/cjs/loader:1155:10)
    at Module.load (node:internal/modules/cjs/loader:981:32)
    at Function.Module._load (node:internal/modules/cjs/loader:822:12)
    at Module.require (node:internal/modules/cjs/loader:1005:19) {
  code: 'MODULE_NOT_FOUND',
  requireStack: [
    'C:\\soft\\nodejs\\node_modules\\npm\\lib\\utils\\unsupported.js',
    'C:\\soft\\nodejs\\node_modules\\npm\\lib\\cli.js',
    'C:\\soft\\nodejs\\node_modules\\npm\\bin\\npm-cli.js'
  ]
}
```

Here is the typical erros log:

```bash
node_modules/@types/node/index.d.ts(6202,55): error TS2304: Cannot find name 'Map'.
node_modules/@types/node/index.d.ts(6209,55): error TS2304: Cannot find name 'Set'.
node_modules/@types/node/index.d.ts(6213,64): error TS2304: Cannot find name 'Symbol'.
node_modules/@types/node/index.d.ts(6219,59): error TS2304: Cannot find name 'WeakMap'.
node_modules/@types/node/index.d.ts(6220,59): error TS2304: Cannot find name 'WeakSet'.
```
The main reason is above stuff are new to ES6, which are unavaiable in ES5. Hold no, you don't need to change your typescript target to ES6, which may break projects and leads to tons of new regression testing.
Firsty, try to add following in tsconfig.json
```json
"lib": ["es2016", "dom"],
```
If no luck, try following in command line, it should resolve this issue.
```bash
$ tsc index.ts --lib "es6"
```
### solutions
This is indicate your nodejs runtime issues, so you can either re-install nodejs or try same command in different nodejs runtime envrionment. For exmaple, run it in WSL (Windows Subsystem for Linux )


## certificate error

Typical errors
```bash
events.js:183
      throw er; // Unhandled 'error' event
      ^

Error: unable to verify the first certificate
    at TLSSocket.<anonymous> (_tls_wrap.js:1103:38)
    at emitNone (events.js:106:13)
    at TLSSocket.emit (events.js:208:7)
    at TLSSocket._finishInit (_tls_wrap.js:637:8)
    at TLSWrap.ssl.onhandshakedone (_tls_wrap.js:467:38)
```
### Solution

add following to https request options
 ,
      rejectUnauthorized: false,
        requestCert: true,
        agent: false

## error ECONNREFUSED
```bash
Error: connect ECONNREFUSED 127.0.0.1:443
    at Object._errnoException (util.js:1022:11)
    at _exceptionWithHostPort (util.js:1044:20)
    at TCPConnectWrap.afterConnect [as oncomplete] (net.js:1182:14)
```
### Solution:
in the http request, do not use 'url' but 'host' and path
host: `xxx.com`,
    port: 443,
    path: `/login`,
