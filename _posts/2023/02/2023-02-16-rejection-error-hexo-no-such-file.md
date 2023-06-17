---
header:
    image: /assets/images/hexo-rejection-error-no-such-file-or-directory.jpg
title:  Fix rejection error in Hexo
date: 2023-02-14
tags:
 - Git
 - script
 
permalink: /blogs/tech/en/hexo-rejection-error-no-such-file-or-directory
layout: single
category: tech
---

> The heart can see what is invisible to the eye.

# Following errors when run `hexo g`

```sh
Unhandled rejection Error: ENOENT: no such file or directory, open '/Users/todzhang/dev/git/blogSrc/themes/next/layout/_scripts/schemes/.swig'
    at Error (native)
    at Object.fs.openSync (fs.js:549:18)
    at Object.fs.readFileSync (fs.js:397:15)
    at Object.ret.load (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/swig/lib/loaders/filesystem.js:55:15)
    at compileFile (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/swig/lib/swig.js:695:31)
    at Object.eval [as tpl] (eval at <anonymous> (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/swig/lib/swig.js:498:13), <anonymous>:338:18)
    at compiled [as _compiledSync] (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/swig/lib/swig.js:619:18)
    at tryCatcher (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/bluebird/js/release/util.js:16:23)
    at null._compiled (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/bluebird/js/release/method.js:15:34)
    at View.render (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/lib/theme/view.js:29:15)
    at /Users/todzhang/dev/git/blogSrc/node_modules/hexo/lib/hexo/index.js:387:25
    at tryCatcher (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/bluebird/js/release/util.js:16:23)
    at /Users/todzhang/dev/git/blogSrc/node_modules/hexo/node_modules/bluebird/js/release/method.js:15:34
    at RouteStream._read (/Users/todzhang/dev/git/blogSrc/node_modules/hexo/lib/hexo/router.js:134:3)
    at RouteStream.Readable.read (_stream_readable.js:336:10)
    at resume_ (_stream_readable.js:733:12)
    at nextTickCallbackWith2Args (node.js:442:9)
    at process._tickCallback (node.js:356:17)

```
#### Solution:

That's because one extra space required after semi colon in _config.yml of Next, as following config

```xml
# Duoshuo ShortName
duoshuo_shortname: cloudsdocker
```

--HTH--



