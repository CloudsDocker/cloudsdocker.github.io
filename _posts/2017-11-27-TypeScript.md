---
header:
    image: /assets/images/hd_typescript.jpg
date: 2022-03-08
title: TypeScript noteworthy notes
tags:
- typescript
- Angular
- JavaScript
layout: posts
category: tech
permalink: /blogs/tech/en/typescript_faq
---
>  The moment you start focusing on yourself, things start falling into place.

# TypeScript Errors

## Cannot use import statement outside a module

When import a module, getting 
```
import generateMsg from '@ovotech/avro-mock-generator'
```

(node:33073) Warning: To load an ES module, set "type": "module" in the package.json or use the .mjs extension.
(Use `node --trace-warnings ...` to show where the warning was created)
/Users/todzhang/dev/workspace/avro-mock-generator/todd.js:1
import generateMsg from '@ovotech/avro-mock-generator'
^^^^^^

SyntaxError: Cannot use import statement outside a module
    at Object.compileFunction (node:vm:352:18)
    at wrapSafe (node:internal/modules/cjs/loader:1026:15)
    at Module._compile (node:internal/modules/cjs/loader:1061:27)
    at Object.Module._extensions..js (node:internal/modules/cjs/loader:1151:10)
    at Module.load (node:internal/modules/cjs/loader:975:32)
    at Function.Module._load (node:internal/modules/cjs/loader:822:12)
    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:77:12)
    at node:internal/main/run_main_module:17:47

### Solutions
To solve this issue, in your package.json file, add `"type": "module"` in the upper level as show below:

{
  "name": "my-app",
  "version": "0.0.0",
  "type": "module",
  "scripts": { ...
  },


## Error: Cannot find package
node:internal/errors:465
    ErrorCaptureStackTrace(err);
    ^

Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@ovotech/avro-mock-generator' imported from /Users/todzhang/dev/workspace/avro-mock-generator/todd.js
    at new NodeError (node:internal/errors:372:5)
    at packageResolve (node:internal/modules/esm/resolve:901:9)
    at moduleResolve (node:internal/modules/esm/resolve:950:20)
    at defaultResolve (node:internal/modules/esm/resolve:1166:11)
    at ESMLoader.resolve (node:internal/modules/esm/loader:536:30)
    at ESMLoader.getModuleJob (node:internal/modules/esm/loader:250:18)
    at ModuleWrap.<anonymous> (node:internal/modules/esm/module_job:79:40)
    at link (node:internal/modules/esm/module_job:78:36) {
  code: 'ERR_MODULE_NOT_FOUND'
}

Node.js v17.6.0

### Solutions
To install the library 

```bash
npm i --save-dev @ovotech/avro-mock-generator
```

## Error:    xx is not a function

TypeError: generate is not a function


# Async Await keywords
Async Await Support in TypeScript
Async - Await has been supported by TypeScript since version 1.7. Asynchronous functions are prefixed with the async keyword; await suspends the execution until an asynchronous function return promise is fulfilled and unwraps the value from the Promise returned. It was only supported for target es6 transpiling directly to ES6 generators.



# Troubleshooting

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
