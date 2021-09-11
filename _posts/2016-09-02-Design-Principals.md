---
title: 漫谈开发设计中的一些‘原则’及'设计哲学'
tags:
- development
- desgin
- principals
- MyBlog
layout: posts
---

在开发设计中有一些常用原则或者潜规则，根据笔者的经验，这里稍微总结一下最最常用的，以飨读者。

# POLA
The principle of least astonishment (POLA) is: "If a necessary feature has a high astonishment factor, it may be necessary to redesign the feature."

In general engineering design contexts, the principle means that a component of a system should behave in a way that users expect it to behave; that is, users should not be astonished by its behavior.

A textbook formulation is: "People are part of the system. The design should match the user's experience, expectations, and mental models."

In more practical terms, the principle aims to leverage the pre-existing knowledge of users to minimize the learning curve, for instance by designing interfaces that borrow heavily from "functionally similar or analogous programs with which your users are likely to be familiar".

## Example:
A web site could declare an input that should autofocus when the page is loaded,[8] such as a search field (e.g., Google.com), or the username field of a login form.

# DRY
这里的DRY是`Do Not Repeat Yourself`的缩写。具体解释参见 ,严谨的定义是　Every piece of knowledge must have a single, unambiguous, authoritative representation within a system，意思是：任何一部分知识在系统中必须只有单一的，清晰并且权威的展示。？？？这是啥意思，没懂。简单说就是不要重复自己任何一部分的工作。比如说，有一段代码是用于清除字条串中的HTML符号，在多个程序中会用到此功能，如果每个地方都使用如下代码
```java
html = html.replaceAll("\\<.*?>","") 
html = html.replaceAll("&nbsp;","");
html = html.replaceAll("&amp;"."");
```
如果是只有２，３个地方用到(Martin曾经提到过Rule of three,意思是一段代码如果被copy３次以上就应该重构到一个单独的子方法中)，你可能就直接复制过来用，但是想想是２，３百个地方用到呢？如果上面需要再做个修改(如下)，你是不是要去这个２，３百个地方去改代码。

```java
html = html.replaceAll("&lt;"."<");
html = html.replaceAll("&gt;".">");
```
所以这个DRY的规则就是推荐使用 `子方法` 的方式，这样只需要修改一次即可. 与之类似的编程思想有 `DIE（Duplication is Evil）,SPoT(Single Point of Truth), SSOT (Singel Source of Truth)` 。 题外话，和DRY对应的是WET,意思是 "write everything twice"（任何东西都写两遍）或者"we enjoy typing" （我们就是喜欢打字编码）。　:-)。

# KISS
KISS 是 Keep it simple, stupid （或者Keep it short and simple ）的简称。意思是在设计时保持简约，通俗。这个很像是现在推畅的“极简风”。
使用KISS有什么好处呢？如下是其中的一些：
- 你可以更快的解决更多的问题
- 你可以使用更少的代码来解决复杂的问题
- 你可以写出更高质量的代码
- 你可以创建更大的系统，更好的去运维
- 你的代码将更加灵活，当有新需求时可以更好的支持扩展，修改或者重构
- 等等

在软件设计领域， 有一些技术具体实现这个精髓，比如 DDD (Domain Driven Design),TDD (Test Driven Develop),这个使代码集中在真正需要的功能上，而不需要其他额外的。另外一个建议是 `不要试图通过注释来提高代码的可读性`，而应该从代码本身提高。比如如下是不太好的变量定义
```java
// i is for 'counter' and j means total sum
int i, j;
```

而如下是好的设计 

```java
// more intuitive one
int counter,sum;
```

与此相呼应的是称作 `奥卡姆剃刀` 或者 `简约之法则`：
> Occam's razor 
> The simplest (explanation|solution) is usually the best one.
> 往往最简单的解决方案是最好的解决方案

具体到以Java为例的程序设计，如下有一些实践KISS的建议
- 首先，认清自己，不要认为自己是个天才，这往往是你犯的第一个错。
- 把你的工作打散成几个子工作，每个部分不会耗费超过4-12个小时去完成
- 把一个问题分成几个小的子问题，每个问题可以通过1个或者只要几个类就能解决。
- 保持每个方法只做一件事，并且不要超过30-40行的代码量
- 保持每个类的体积不要太大。
- 不要害怕扔掉不用的代码。就像家里用不到的东西就及时扔掉一样。

# New Jersey style （Worse is better）
新泽西风格，也叫做“Worse is better”。此原则指出，`系统的质量不会因为新功能的增多而提高`。 比如一个软件，只提供一些功能，但是用户很方便使用，有可能比一些提供了非常多令人眼花缭乱功能的“大杂烩”似的软件。比如像 Linux下面的 vi/vim, 浏览器中的Chrome.

# SOLID
SOLID是几个编程哲学的总称，即 SOLID (Single responsibility, Open-closed, Liskov substitution, Interface segregation and Dependency inversion) ，下面我们分别解释一下：
## Single responsibility （SRP）
单一功能原则。Robert描述这个为“A class should have only one reason to change.”，即修改一个类（或者模块）有（且只能有）一个理由。简单说就是 `一个类或者模块只能负责一个功能`。举个例子，有一个模块负责生成一个报表，可以想像可能有两个理由去修改此模块，第一，报表的内容要变，第二，报表的格式要改。这两个改动是出于不同的理由，一个是内容的一个美化版面的。 而 “单一职责” 规则认为这是两个不同的职责，因此应该分成两个不同的子模块。如果把两件事情放在一起，并且不同的改动是出于不同的原因，这种设计是不好的。此规则方便系统各模块间解耦合。
## Open/closed principle （OCP）
开闭原则。Bertrand描述为“"software entities (classes, modules, functions, etc.) should be open for extension, but closed for modification";”，也就是说对于一个实体（类，模块，方法等）允许在不修改源代码的前提下扩展它的功能行为。即，你可以把 `新代码放到新的类或者方法中`，新类通过继承来重用已有代码及功能。而 `已有的代码只有在修bug时才去修改`。 此原则主要用于降低在添加新加功能时引入新的bug的风险。
## The Liskov Substitution Principle （LSP）
里氏替换原则. 原文是 “Derived classes must be substitutable for their base classes.”，意思是，`派生类（子类）对象能够替换其基类（超类）对象被使用`。 比如说，如果 S 是T 的子类， 那么任何T类的具体实现对象都可以替换S的实现对象出现的地方，具体的调用者也不知道具体是父类还是子类，还不会出现任何错误。比如下图，调用者可以2来替换1的地方 。
![](https://msdnshared.blob.core.windows.net/media/TNBlogsFS/BlogFileStorage/blogs_msdn/willy-peter_schaub/WindowsLiveWriter/SDLCSoftwareDevelopmentLifecycleflashbac_A707/image_4.png)
## Interface segregation principle （ISP）
接口隔离。原文是 many client-specific interfaces are better than one general-purpose interface. 意思是多个特定客户端接口要好于一个宽泛用途的接口。Make fine grained interfaces that are client specific. 应该定义粒度合适的一系列接口(像下图)，以便于每个客户去实现具体的功能请求。换句话说是，客户（client）不应该必须去依赖于它用不到的功能方法。此原则的目的是系统解开耦合，从而容易重构，更改和重新部署。
![](http://cdn.hackerchick.com/wp-content/uploads/2010/04/200806SOLIDIISP2.gif)

## Dependency inversion principle (DIP)
依赖反转原则. 原文是 One should “Depend upon Abstractions. Do not depend upon concretions.” 意思是 一个方法应该遵从“依赖于抽象而不是一个实例”。该原则规定：

1. 高层次的模块不应该依赖于低层次的模块，两者都应该依赖于抽象接口。
1. 抽象接口不应该依赖于具体实现。而具体实现则应该依赖于抽象接口。
这个就像是设计模式中的Adaptor适配器模式。
下图解释了这个原理。
[](https://upload.wikimedia.org/wikipedia/commons/9/96/Dependency_inversion.png)
图1中，高层对象A依赖于底层对象B的实现；图2中，把高层对象A对底层对象的需求抽象为一个接口A，底层对象B实现了接口A，这就是依赖反转。

# SOC
Separation of concerns,?即关注点分离。 是处理复杂性的一个原则。由于关注点混杂在一起会导致复杂性大大增加，所以能够把不同的关注点分离开来，分别处理就是处理复杂性的一个原则，一种方法。这个与SOLID中的 SRP很类似。

# YANGI
是"You aren't gonna need it"的缩写，直译是“你将来用不到它的”。这个是[极限编程](https://en.wikipedia.org/wiki/Extreme_programming)的一个编程思想。意思是说,永远不要因为 `预计`你会用到某个功能就去写一段代码去实现，总是只有问题出现了，`真的需要这个功能时才去写`。

# 参考
- https://en.wikipedia.org/wiki/Principle_of_least_astonishment
- [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [ 六大设计原则--里氏替换原则【Liskov Substitution Principle】](http://blog.csdn.net/sinat_20645961/article/details/47393737)
- [SOLID](https://en.wikipedia.org/wiki/SOLID_(object-oriented_design))
- [how to keep code simple](http://stackoverflow.com/questions/816130/how-to-keep-my-code-simple)
- [奥卡姆剃刀](https://en.wikipedia.org/wiki/Occam%27s_razor)
- [Apache KISS](http://people.apache.org/~fhanik/kiss.html)
- [Worse is better](https://en.wikipedia.org/wiki/Worse_is_better)

