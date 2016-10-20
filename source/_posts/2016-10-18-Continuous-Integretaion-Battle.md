---
title: Battle of CI(Continuous Integration) flagship tool 持续集成工具扛把子之争
tag:
- CI
- DevOps
---

# 引言
有句话说`有人的地方就有江湖`，同样，有江湖的地方就有恩怨。在软件行业历史长河（虽然相对于其他先来来说，软件行业的历史实在太短了，但是确是十分的精彩）中有一些分分合合的小故事，比如类似的有，从一套代码发展出来后面由于合同到期就分道扬镳，然后各自发展成独门产品的Sybase DB和微软的SQL Server；另外一个例子是，当时JBPM的两个主要开发的小伙伴离开当时的Red Hat，在JBPM基础上自立门户新创建的Java工作流管理软件Activiti，等等。在持续集成工具龙头老大这个宝座，也曾经发生过吵架分家，再对着干的事情，今天分享一下这信有趣的故事。

# DevOps
首先，防止`先入为主`,以为大家都知道这个那个的。先普及下相关背景知识，如果已经了解的同学可以跳过。目前在软件工程领域已经火了好几年的`DevOps`领域，核心的模块就是`CI`与'CD'，即Continuous Integration与Continuous Deployment,也就是持续集成与持续部署，这个对于处于`敏捷`开发环境下尤其是互联网等需要高速迭代是个核心的功能，可以说没有CI，就不可能达到像Google或者Facebook这些一天有多个release的情况。

# CI
CI(Continuous Integration) 持续集成起源于 XP(极限编程)与 TDD (Test Driven Develop)以测试驱动的开发模式，是防止出现所谓的'集成地狱',即防止程序员在正常编码工作中新引入的bug。CI会持续的（重复的）进行一些小的工作，比如跑测试用例，扫描代码，等工作。市场上有很多的CI解决工具，常用的如下几个，

![  ](http://logz.io/wp-content/uploads/2016/02/travis-ci.jpg)
![Jenkins](http://www.datical.com/wp-content/uploads/2014/08/Jenkins-Logo.png)
![  ](https://448bb31d92917ba3390f-4a8f48d20b0d8c78b979208d38d37653.ssl.cf1.rackcdn.com/677/screenshots/butler1000.jpg)


### Travis


基工作原理大同小异，比如下图，一个典型的用例是
- 程序员在本地开发完成后把代码提交到VCS (Version Control System)比如SVN, Git, Perforce, RTS等
- CI工具发现有新的check in (有很多不同的配置，比如除了监视VSC外还可以使用CRON等配置比如每隔一个小时启动一次，或者每两次check in 启动一次，等等)自动启动去抓取最新的代码
- CI可以配置使用集群的编译机器，去选择最合适的机器（有不同的策略，比如找到最清闲或者离代码距离最近的机器）来编译源代码
- 根据不同的配置，CI有可能会调用配置好的测试用例，如果测试失败，根据策略（比如少于几个错误就先忽略）要么通知用户，要么继续跑测试用例
- 根据配置，CI可能会去执行其他操作，比如静态源代码分析，如代码有没有不符合公司安全要求，把连接密码写在代码里面等等，还有比如生成文档，测试报告，等。
- 如果所有定义好的jobs跑完，去生成最终报告并送给用户
- 生成一些分析报表，比如最近成功率，最近哪些程序员造成的错误最多等等。
- 一些高级的CI,比如Jenkinsg还支持自定义扩展，也会去按配置去执行。



![jenkins-plugin-diagram-saci](http://agilelucero.com/wp-content/uploads/2014/03/jenkins-plugin-diagram-saci.png)

http://image.slidesharecdn.com/continuousintegration-100503045436-phpapp01/95/continuous-integration-system-6-728.jpg?cb=1272862514

http://decks.eric.pe/pantheon-ci/images/ci-architecture-pantheon.png

这其中如果任何一步出现了错误，比如某个程序员在提交代码时忘记同时提交一个新写的类，造成失败，首先在CI（比如Jekins，或者Travis）上会显示错误 （比如下图），同时还可以配置CI工具会发出邮件提醒，甚至可以根据提交信息智能的显示出来是哪个程序员搞砸的。

![](https://www.packtpub.com/sites/default/files/Article-Images/0082OS_02_14.png)

- 配置CI工作去预订并监视SCM (比如Git等)Continuous Integration is a development practice that requires developers to integrate code into a shared repository. Each time developer checks in code into the repository, it is then verified by an automated build process. This process gives flexibility for the developer to detect any build issues early in the build life cycle.
- 
- 

# Reference
- [CI in wikipedia](https://en.wikipedia.org/wiki/Continuous_integration)