---
title: NodeJs Notes
tags:
- NodeJs
- Angular
layout: posts
---

## commands to read files
 var lineReader = require('readline').createInterface({
    input: require('fs').createReadStream('C:\\dev\\node\\input\\git_reset_files.txt')
 });

 lineReader.on('line', function(line){
    console.log('git checkout '+line);
 });

