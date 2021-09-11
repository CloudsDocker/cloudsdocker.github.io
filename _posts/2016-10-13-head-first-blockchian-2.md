---
title: 【原创】深入浅出区块链系统：第二章
tags:
 - blockchain
 - ethereum
 - MyBlog
layout: posts
---


> 使用Solidity创建以太坊(Ethereum)智能合约(Smart Contract)

# 引言
前面第一章 ([位于微博上的链接](http://weibo.com/ttarticle/p/show?id=2309404030129192967736#_0))主要介绍了区块链的概念，我们知道区块链分为两大类，一是以公有链为代表的`无权限控制区块链`，第二是`有权限控制的区块链`，这个又包括了`私有链`(Private Blockchain,以Overstock为代表)和`联盟链`(Consortium Blockchain,以R3为代表)，相对于公有链来说，这些链一般都是没有电子货币，因为他们不需要像公有链那样要靠电子货币作为挖矿的奖励来激励参与，所以速度也是比较快的。

上一章都是讲的抽象的概括，下面我们就深入讲一些具体的东西，这样以便于大家有一个形象的概念，方便理解。我们这一章主要讲讲公有链，以方便讲解以及大家去继续研究，尝试，这里选择在公有链领域社区最为活跃以太坊（Ethereum），对于中国用户来说，其于2016年9月19号刚刚在中国上海举办了DevCon 2区块链峰会，很多人可能有所印象。第一步，这个东西怎么读啊？其实这是新构造的一个单词，而非一个已有的英语单词，其读作[i'θi:'riəm]。接下来我们会一起过一下涉及的一些概念，后面我会介绍几个如何进行太坊开发的技术工具，以及两个比较好用的应用框架。

大家都知道，学习一个新技术最好的方式就是亲自动手试一把，几乎学习所有新编程语言上来都会写个`HelloWorld`并运行一把，在这一章最后一部分我会手把手的带领大家创建并运行一个智能合约。

# 概念

## Ethereum:

Ethereum ([官方链接](https://www.ethereum.org)) ，是个区块链公有链解决方案，如果比特币的区块链称作区块链1.0的话，那Ethereum可以称为区块链2.0 。 其主要特色就是支持`可编程`的智能合约。这个开源的系统相当于计算机中的操作系统一样，其是一个平台，提供了API及接口，以供其上运行不同的程序共享使用。同时因为它本质上是`去中心化的区块链`，因此号称是零宕机，零审查，以及不会有欺诈与人为篡改。就像所有的公有链需要激励机制的“代币”一样，它除了底层的区块链外，还有自己的加密电子货币，Ether，即`以太币`，在国内有些人戏称为“姨太”。目前一个“姨太”大约11美元，实时的价格趋势可以参见 [这个交易所链接](https://www.coingecko.com/en/price_charts/ethereum/usd)

![](http://cloudsdocker.github.io/images/EtherUSD.png)

## 智能合约

智能合约 ([解释链接](https://en.wikipedia.org/wiki/Smart_contract) )，其实这个概念本身是远远早于区块链产生的（早在1994年就出现了）。智能合约，说白了就是自己写的一段代码放到区块链上，在这里可以添加自己需要的业务逻辑等，只是这段代码在创建后不像传统应用是部署到服务器上运行，而是放到区块链上，并且自动执行(其运行部署都会消耗Gas(气，也就是若干的以太币))。各个参与方不需要像以前需要一个或若干个中心节点/服务器，大家都各自在自己那里完全按照“合约”执行，中间没有人可以去篡改或者停止，此设计会大大提高flexibility(灵活性）以及互相不信任的问题。比如有一个智能合约定义的逻辑是：当A收到钱后，B就会收到货物，这些操作都是按照合约自动执行，中间不再会有违约或者被人为修改的风险。

这些智能合约是以DAPP (Decentralized  Application)的形式存在。智能合约是部署在区块链上，由于区块链的透明性，这些合约对任何人都是可见的，当然这个有利有弊。如果其有bug或者漏洞，就有可能被人抓住并利用，比如2016年6月的The DAO攻击，就造成相当于5千万美元的以太币丢失，这也直接导致了以太坊后面的一次更分叉，这块笔者后面会撰文详解。

## Web 3.0
大家可能听说过web 1.0， 其是指之前传统的网页技术，比如HTML，传统的JavaScript,VBScript,CSS。而web 2.0 是使用所谓的DHMTL,HTML5, Ajax,等众多的JavaScript技术，来创作类似于桌面程序效果般的网页应用。Web 2.0这些技术有个问题，就是`过于依赖`中心化的服务器/第三方机构，比如除了其应该做的提供网页访问服务外，还有验证，用户行为记录分析等。 而这里提出的web 3.0是有如下几个特性，首先是`去中心化`，比如通用的后台端，使用Swarm与bzz来作为`内容寻址的存储系统`，基于区块链的`共识形成机制`，基于Whisper的异步消息机制等，这样具体的业务逻辑都会分发到每个客户端去执行，而非位于昂贵且易于出问题的少数中心节点。 

这是刚刚提到的架构图

![](https://blog.ethereum.org/wp-content/uploads/2016/07/Screen-Shot-2016-07-08-at-5.37.32-PM.png) 


## Solidity
上面说到的这些智能合约一般来说是使用一种特殊的编程语言来创建的，即Solidity，这个语言是以太坊提出并创造的，面向对象的DSL特定领域编程语言(Domain Specific Language),它是以太坊支持的4种语言（另外三个是Serpent, LLL 和 Mutan），只不过其是最流行的一个语言。从技术上来讲，solidify源代码会编译成字节码，然后运行于EVM（Ethereum Virtual Machine）上面。如果你看到源代码后就会觉得其实Solidity是与JavaScript十分类似的语言，如下是一段代码：

![](http://cloudsdocker.github.io/images/Solidity.png)

Gavin Wood (Solidity之父)说Solidity就是根据ECMAScript（是JavaScript,ActionScript等的标准祖先）所创建的，这样对于大多数开发人员来说学习曲线会很平滑。

# 开发工具

由于发展时间不是很长，目前市面上可用的开发环境IDE不太多。下面介绍下稍微比较成熟可靠的开发工具。

## Microsoft Visual Studio Ethereum 插件

没错，就是那个市面上已经非常常见的visual studio，也就是dot net的开发工具，不是一个全新的开发工具。此开发集成环境只需要安装solidify插件即可。 这个也从侧面可以看到微软对于以太坊以及区块链的野心。

安装此插件后在微软的Visual Studio后就可以在新建项目时的模板里看到这个Solidity 选项：

![](http://cloudsdocker.github.io/images/VisualStudio-Overview.png)

当选择此模板后，visual studio他会自动构造出一个应用的基本文件结构。这样你可以省去一些每次开发一个智能合约都要重复的工作。你就可以集中时间精力到真正业务代码上。

如下就是这个IDE自动生成的代码

![](http://cloudsdocker.github.io/images/VisualStudio-Outline.png)

## Ethereum Studio 

除了背靠微软这个大旗的visual studio集成开发环境外，还有一个方便大家使用的免费的IDE。这个是基于Cloud9平台的一个在线IDE，其完全运行于浏览器中，不用安装，可以用于任何的操作系统。如下就是这个在线集成开发环境的样子。这个还是比较推荐的开发环境：

![](http://cloudsdocker.github.io/images/Cloud9.png)


# 智能合约应用开发框架

目前比较常用的智能合约构架有如下几个，都是开源并且免费的。这里我们来手把手的创建并运行一个智能合约，来体会一下。

## Embark

首先推荐的是这个叫做Embark的框架，他是一个让你可以轻松开发部署Dapps的平台，它支持的功能包括，在JS代码中部署智能合约，智能合约的热部署，可以集成grunt等构造工具。支持TDD（即测试驱动的开发）比如支持mocha等测试框架，可以方便的使用IPFS等去中心化的系统，支持增量，智能的部署修改过的智能合约等。这个工具是使用nodejs写的，因此你需要先安装nodejs的环境。这个平台会在你本地启动一个区块链服务模拟器，这样你就可以完全在本地开发测试，大大提高了工作效率。如下是启动后的截图。Embark的安装及源代码位于[Gitub这里](https://github.com/CloudsDocker/embark-framework)

首先你需要来安装Embark以及区块链模拟器。

```sh
# 安装Embark
npm -g install embark-framework

# 安装区块链模拟器
npm -g install ethersim

# 启动RPC模拟器
embark simulator
```

启动的模拟器是下面这个样子
![](http://cloudsdocker.github.io/images/Ethersim.png)

然后我们去创建一个新的智能合约：

```sh
# 创建一个叫做demo的智能合约基础结构
embark demo
# 进入这个目录，下面含有配置文件 embark.yaml
cd embark_demo
# 启动应用
embark run
```
启动后,首先在后台看，Emark帮忙使用coffee script等构造并部署了合约。

![](http://cloudsdocker.github.io/images/EmbarkStart.png)

你可以使用浏览器试验一下，比如打开`http://localhost:8000`，然后你可以试着输入个数值，去试试看看它是不是已经能够响应处理你的输入了：

![](http://cloudsdocker.github.io/images/EmbarkApp.png)

是不是很神奇，短短两三分钟，已经从零开始构造出一个可以运行的以太坊DAPP
，并运行于区块链之上。 接下来我们介绍另外一个框架选择方案。

## Truffle

Truffle,是跟前面提到的 Ethereum Studio 同一个公司（ConsenSys）开发的一个框架， 这个跟前面的embark类似，也是可以提供一个智能合约的开发测试平台,他的一个特色就是它可以集成nodejs里面强大的测试功能，比如Mocha, Chai等等. 像Embark一样，你需要另外安装运行其他软件，来启动以太坊客户端模拟器，最常用的是EthereumJS TestRPC  [Github link](https://github.com/ethereumjs/testrpc), 它会在内存中启动一个Ethereum的客户端， 这样可以快速测试你开发的应用。

因为这个也是使用nodejs创建的应用，因此使用如下命令来安装此程序，安装好了启动此应用

```sh
#安装以太坊模拟器
npm install -g ethereumjs-testrpc
# 启动模拟器
testrpc
```

启动后是这样子的
![](http://cloudsdocker.github.io/images/Testrpc.png)

模拟器启动好了，接下来执行下面的命令来初始化truffle应用。
```sh
mkdir firstApp
cd firstApp
truffle init
```
上面最后一个命令就会自动帮你构造好的程序框架，包括一些最基本的JavaScript文件，几个智能合约源代码，主应用程序的HTML代码及配套的CSS等文件 。如下是这个基本框架：
![](http://cloudsdocker.github.io/images/Truffle_Window.png)

接下来你可以添加自己的代码到`contracts`目录下的智能合约文件，也可以什么都不动，因为truffle已经自动生成了最基本的框架。

```sh
#这个命令会把智能合约源代码编译成字节码
truffle compile
```

编译好的代码需要部署到区块链上才可以执行，在truffle中这个工作是由`migrates`目录下定义的migrate作业执行的，我们去修改文件`2_deploy_contracts.js`为如下：
```javascript
module.exports = function(deployer) {
  // deployer.deploy(ConvertLib);
  // deployer.autolink();
  // deployer.deploy(MetaCoin);
  deployer.deploy(HelloEthereum);
};
```

然后执行如下命令去执行代码部署，它除了把你的智能合约发布到区块链之外，还会做一些相关工作，比如link用到的library等。deployer可以使用`promise`的方式 (e.g. .then(function(xx)))来执行其他额外的工作等，比如创建一个其他的合约并调用，等。这个便于你来灵活的扩展应用。
```sh
truffle migrate
truffle build
```

# 结语

好了，至此我们已经了解了什么是以太坊已经其上运行的智能合约，DAPP等概念。后面又介绍了开发智能合约的工具已经可复用的框架，最后又手把手亲自做了一个智能合约。这样大家应该对区块链以及以太坊等公有链有了一个形象具体的感觉了吧。如果这里有什么问题或者建议，欢迎通过下面的联系方式与我沟通。


# Referece
- [Introduction to Smart Contracts](https://solidity.readthedocs.io/en/develop/introduction-to-smart-contracts.html)
- [Installing Solidity](https://solidity.readthedocs.io/en/develop/installing-solidity.html)
- [以太坊官方教程](https://blog.ethereum.org/2016/07/12/build-server-less-applications-mist/)
- [Swarm](http://swarm-gateways.net/bzz:/swarm/)
- [Truffle Official Doc](http://truffle.readthedocs.io/en/latest/)


## 联系我：
* phray.zhang@gmail.com (email/邮件，whatsapp, linkedin)
* helloworld_2000 (wechat/微信)
* [github](https://github.com/CloudsDocker/)
* [简书 jianshu]（http://www.jianshu.com/users/a9e7b971aafc）
* 微信公众号：vibex
* [webo/微博](http://weibo.com/cloudsdocker): cloudsdocker
