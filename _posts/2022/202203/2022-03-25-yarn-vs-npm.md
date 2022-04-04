---
header:
    image: /assets/images/yarn_npm_install.jpg
title:  Tell me difference of yarn install and npm install in short answer
date: 2022-03-25
tags:
 - Yarn
 - npm
 - node
 
permalink: /blogs/tech/en/node_vs_npm_install
layout: single
category: tech
---

> Don't find fault. Find a remedy.

# yarn install vs npm install

When we run npm install , the dependencies are installed sequentially, one after another. The output logs in the terminal are informative but a bit hard to read. To install the packages with Yarn, we run the yarn command. Yarn installs packages in parallel, which is one of the reasons it's quicker than npm.

# yarn why 
To show a Library loaded as dependencies
```bash
yarn why redux
yarn why v1.22.18
[1/4] 🤔  Why do we have the module "redux"...?
[2/4] 🚚  Initialising dependency graph...
[3/4] 🔍  Finding dependency...
[4/4] 🚡  Calculating file sizes...
=> Found "redux@4.1.2"
info Has been hoisted to "redux"
info Reasons this module exists
   - Specified in "dependencies"
   - Hoisted from "react-beautiful-dnd#redux"
   - Hoisted from "react-beautiful-dnd#react-redux#@types#react-redux#redux"
info Disk size without dependencies: "240KB"
info Disk size with unique dependencies: "1.06MB"
info Disk size with transitive dependencies: "1.1MB"
info Number of shared dependencies: 2
✨  Done in 0.34s.
```

# skip optional

In some extents, maybe for performance perspective or errors in some non-mandatory library, you can skip those optional libraries during install. For example,  `fsevents` is dealt differently in mac and other linux system. Linux system ignores fsevents whereas mac install it. As the above error message states that fsevents is optional and it is skipped in installation process.

```bash
You can run npm install --no-optional
```

# Why node-gyp used in nodejs
Basically, node-gyp is like make. It's a tool used to control the compilation process of C++ projects. Only, it's designed specifically for node.js addons (modules written in C++). So moving to a different system may work if it uses the same CPU. Moving to a different OS or CPU (for example from x86 to ARM) won't work. For Linux, moving to a different distro of different version of the same distro may or may not work. I'm not 100% sure if moving to a different version of node.js would work


node-gyp is a tool which compiles Node.js Addons. Node.js Addons are native Node.js Modules, written in C or C++, which therefore need to be compiled on your machine. After they are compiled with tools like node-gyp, their functionality can be accessed via require(), just as any other Node.js Module.

--End--



