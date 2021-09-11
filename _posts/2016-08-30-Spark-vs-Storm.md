---
title: Spark-vs-Storm
tags:
 - Spark
 - Storm
 - Apache
 - Haddop
 - BigData
layout: posts
---
The stark difference among Spark and Storm. Although both are claimed to process the streaming data in real time. But Spark processes it as micro-batches; whereas Storm processes per message - meaning if you intend to process things like social data, log data, etc.. you can actually apply CEP (Complex Event Processing) per tuples (i.e each social message in your example).  Spark, on other hand is good at processing small blocks of data, for instance if you are streaming a whole blobs of data (say some huge files of medical record, for example).

So, obviously, I would say, give your usecase, Storm may be a better fit for your needs.

And last, between distributions, I have found Hortonworks to be more easier in standing up and managing the cluster than other distribution (please take this comment with a grain of salt, as I may be slightly biased towards HWX given my comfort-zone of working around this distribution more than others)
