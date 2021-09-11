---
layout: posts
title: git raise error filename too long when checkout
tags:
 - Git
 - DevOps
---

# Symptoms:

node_modules/grunt-contrib-imagemin/node_modules/pngquant-bin/node_modules/bin-wrapper/node_modules/download/node_modules/request/node_modules/form-data/node_modules/combined-stream/node_modules/delayed-stream/test/integration/test-handle-source-errors.js: **Filename too long**


# solution

1. Execute following command
```sh
git config core.longpaths true
```
1. retry checkoutpap
