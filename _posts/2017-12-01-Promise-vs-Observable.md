---
title: promise vs observiable
tags:
- Angular
- JavaScript
layout: posts
---

The drawback of using Promises is that they’re unable to handle data sources that produce more than one value, like mouse movements or sequences of bytes in a file stream. Also, they lack the ability to retry from failure—all present in RxJS. 


The most important downside, moreover, is that because Promises are immutable, they can’t be cancelled. So, for instance, if you use a Promise to wrap the value of a remote HTTP call, there’s no hook or mechanism for you to cancel that work. This is unfortunate because HTTP calls, based on the XmlHttpRequest object, can be aborted,[3] but this feature isn’t honored through the Promise interface


