---
title: Battle of CI(Continuous Integration) flagship tool 持续集成工具扛把子之争
tag:
- CI
- DevOps
---

# 引言
有句话说`有人的地方就有江湖`，同样，有江湖的地方就有恩怨。在软件行业历史长河（虽然相对于其他先来来说，软件行业的历史实在太短了，但是确是十分的精彩）中有一些分分合合的小故事，比如类似的有，从一套代码发展出来后面由于合同到期就分道扬镳，然后各自发展成独门产品的Sybase DB和微软的SQL Server；另外一个例子是，当时JBPM的两个主要开发的小伙伴离开当时的Red Hat，在JBPM基础上自立门户新创建的Java工作流管理软件Activiti，等等。在持续集成工具龙头老大这个宝座，也曾经发生过吵架分家，再对着干的事情，今天分享一下这信有趣的故事。

# DevOps
首先，防止`先入为主`，先普及下相关背景知识，如果已经了解的同学可以跳过。目前在软件工程领域已经火了好几年的`DevOps`领域，核心的模块就是`CI`与'CD'，即Continuous Integration与Continuous Deployment,也就是持续集成与持续部署，这个对于处于`敏捷`开发环境下尤其是互联网等需要高速迭代是个核心的功能，可以说没有CI，就不可能达到像Google或者Facebook这些一天有多个release的情况。

# CI
CI(Continuous Integration) 持续集成起源于 XP(极限编程)与 TDD (Test Driven Develop)以测试驱动的开发模式，是防止出现所谓的'集成地狱',即防止程序员在正常编码工作中新引入的bug。CI会持续的（重复的）进行一些小的工作，比如跑测试用例，扫描代码，等工作。比如，一个典型的用例是。

- 配置CI工作去预订并监视SCM (比如Git等)
- 
- 

# Reference
- [CI in wikipedia](https://en.wikipedia.org/wiki/Continuous_integration)