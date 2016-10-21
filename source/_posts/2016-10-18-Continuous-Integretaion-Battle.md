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


# CI 的进化史
世界上本来没有CI,用的人多了也就成就了CI。本来软件工程里是没有这个概念的。每个程序员自己做自己的开发，然后团队把代码放在一起，然后build，再自己或者单独的测试团队去测试，没有问题部署。这些都是或多或少由人手工去做的。但是就是很多人类的发明就是为了人类"偷懒"一样，CI慢慢在一些想偷懒的牛人脑子里形成。这其中就有Kent Beck （多说一句，这个现在工作于Facebook的牛人创造了很多到现在还在流行的东西，比如Agile敏捷开发，以JUnit为代码的xUnit测试理念，TDD测试驱动开发等等），在上个世纪最后几年，Kent Beck创造了XP，注意这个不是Bill的那个XP操作系统，是eXtreme Programming，即极限编程。虽然现在看起来极限编程有很多很诡异不太现实的方式，比如两个程序员坐在一起，使用一台电脑一起写一段程序等天马行空的想法。但是其中一个理念就是“持续集成”（CI)。以此理念，后面出现了使用各种语言写的CI的工具，其中的老大是CruiseControl。

到了2005年，当时就职于Sun的一个叫川口浩介（Kohsuke Kawaguchi）的日本人，重新“发明轮子”，不顾如日中天的CruiseControl，设计并开发了一个新的持续集成的软件，起名叫做Hudson。它提供了很多强大的功能，比如提供插件机制，这样就使其几乎集成了市面上所有的SVN，CVS, Subversion, Git, Perforce等。另外，它还提供了界面扩展能力，另外还支持基于Apache Ant and Apache Maven的项目，除了xNix,还支持Windows环境等一众强大功能。很快，在大约2007年的时候Hudson已经超越CruiseControl。然后在2008年5月的JavaOne大会上，Hudson获得了开发解决方案类的Duke's Choice奖项。从此，小弟翻身做大哥，Hudson成为CI的代名词。其主要开发者 Kohsuke Kawaguchi 还获得了Google-O'Reilly Open Source Award。后来也不用自己苦逼的写代码了，只要到处受邀去演讲做是如何受什么启发创造并发明了这么好的工具，造福大批程序员。其后来还创立了CloudBees，出任CEO，迎娶白富美，走上人生新巅峰。

一切看起来都是那么美好。但是在2009年6月，Oracle收购Sun，所有人都蒙逼了，是不是写反了？一个传统数据库的公司收购了在Java及开源老大的Sun。然后，其内部各个产品及项目就被整合，调整。这也就算了，反正谁给钱不是干活哪，但是在2010年9月，Oracle竟然暗戳啜的把Hudson变成了注册商标。2010年11月，Hudson社区的核心开发人员发现了，他们觉得这对于一个一直标榜自己是开源CI工具的Hudson来说是个玷污。双方进行了的会谈，过程不太不太友好，然后就不出意料的谈崩了。2011年圣诞节过后，几个秃顶的大叔觉得不要再跟Oracle的律师在这里瞎扯淡了，他们决定自立门户，自己起个新的名字叫Jenkins。然后凑钱注册网址，买服务器，列出下面的清单，统统改名，
- hudson-labs.org -> jenkins-ci.org
- @hudsonci -> @jenkinsci
- http://github.com/hudson -> http://github.com/jenkinsci
- hudson-dev -> jenkins-dev
- hudson-users -> jenkins-users
- hudson-commits -> jenkins-commits
- hudson-issues -> jenkins-issues

然后把代码fork出一份来（好笑的是Hudson说Jenkins都声称是对方是自己这里的子分叉），所以你可以看到Hudson与Jenkins的界面都十分类似。

## Jenkins的界面
![](http://jenkins-debian-glue.org/img/jenkins_jobs.png)

## Hudson的界面
![](hudson_gui.jpg)

但是有一个值得注意的地方就是两个系统的logo，其中Hudson是一个高傲的老头子，而Jenkins是一个谦卑为你服务的老头子。

![Jenkins](http://www.datical.com/wp-content/uploads/2014/08/Jenkins-Logo.png)
![  ](https://448bb31d92917ba3390f-4a8f48d20b0d8c78b979208d38d37653.ssl.cf1.rackcdn.com/677/screenshots/butler1000.jpg)


分家之后，Hudson有Oracle和Sonatype's corporate的支持和Hudson的注册商标，而Jenkins拥有的是大多数的核心开发者，社区，和后续更多的commit。比如下图是分家之后两个软件的对比。

![](hudson_vs_jenkins_submit.png)

# CI持续集成的工作原理

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