---
title: How to setup nodejs to install package from intranet
tags:
- nodejs
- angular
- javascript
layout: posts
---

# Error of 'ECONNRESET'
You may face error `ECONNRESET` from intranet, even appropriate proxy tools (e.g. cntlm) is running. The errors may looks like
```bash
$ npm install -g @angular/cli@latest
npm WARN registry Unexpected warning for http://registry.npmjs.org/: Miscellaneous Warning ECONNRESET: request to http://registry.npmjs.org/@angular%2fcli failed, reason: read ECONNRESET
npm WARN registry Using stale package data from http://registry.npmjs.org/ due to a request error during revalidation.
npm ERR! code ECONNRESET
npm ERR! errno ECONNRESET
npm ERR! network request to http://registry.npmjs.org/@angular-devkit%2farchitect failed, reason: read ECONNRESET
npm ERR! network This is a problem related to network connectivity.
npm ERR! network In most cases you are behind a proxy or have bad network settings.
npm ERR! network
npm ERR! network If you are behind a proxy, please make sure that the
npm ERR! network 'proxy' config is set properly.  See: 'npm help config'

npm ERR! A complete log of this run can be found in:
npm ERR!     C:\Users\xxx\AppData\Roaming\npm-cache\_logs\2018-05-15T05_04_39_505Z-debug.log
```

## resson
You need to update npm configuration to make sure below config presence 
* registry
and config `https-proxy` should NOT exist. 

You can run following command to remove it
* https-proxy

## You can check your current config as 
```bash
npm config list
```

## To fix above issues, please run following commands
```bash
npm config delete https-proxy
```

# Error of 'code E503'

Sometimes when you run npm install, you can see error 'E503'. 
```bash
$ npm install -g @angular/cli@latest                                            npm WARN registry Using stale package data from http://registry.npmjs.org/ due to a request error during revalidation.
npm ERR! code E503
npm ERR! 503 Service Unavailable: @angular-devkit/architect@0.6.0

npm ERR! A complete log of this run can be found in:
npm ERR!     C:\Users\xxx\AppData\Roaming\npm-cache\_logs\2018-05-15T05_40_53_127Z-debug.log

```
That's because property 'proxy' missing for npm. Please run below command to check wether it's exist or not.

```bash
npm config list | grep 'proxy'
```

If not exist, run below command to add it back.
```bash
npm config set proxy http://127.0.0.1:53128
```
