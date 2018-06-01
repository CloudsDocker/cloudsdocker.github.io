---
title: Node errors troubleshooting
---

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
