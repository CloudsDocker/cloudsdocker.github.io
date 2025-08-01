---
title: 浅谈软件单元测试中的“断言” (assert)，从石器时代进步到黄金时代。
tags:
 - java
 - testing
 - MyBlog
layout: posts
---

大家都知道，在软件测试特别是在单元测试时,必用的一个功能就是“断言”（Assert)，可能有些人觉得不就一个Assert语句，没啥花头，也有很多人用起来也是懵懵懂懂，认为只要是Assert开头的方法，拿过来就用。一个偶然的机会跟人聊到此功能，觉得还是有必要在此整理一下如何使用以及对“断言”的理解。希望可以帮助大家对此有一个系统的理解，也趁机聊聊“断言”发展一路过来的心路历程。

# 基础知识
首先稍微介绍一下断言相关知识，对于有经验的程序员请移步到下面的“断言”进化史部分。


## 什么是断言
在单元测试时，程序员预计在程序运行到某个节点位置，需要判断某些逻辑条件必须满足，这样下面的一些业务逻辑才可以进行下去，如果不满足，程序就会"报错"甚至是"崩溃"。比如说，一段程序是负责“转账”，在真正开始转账操作前首先需要“断言”这个账户是一个“合法”的账户，比如账户不是`null`。当出现些状况时，程序开发人员就可以在第一时间知道这个问题，可以去`debug`除错，而非等到交付给用户后才发现问题。其实这个功能是TDD (Test Driven Develop)的基石之一。

## “断言” vs "异常"或者错误， 即 Assert vs. Exception/Error
- “断言”通常是给程序开发人员自己使用，并且在开发测试期间使用。而异常等在程序运行期间触发
- 通常“断言”触发后程序“崩溃”退出，不需要从错误中恢复。而“异常”通常会使用try/catch等结构从错误中恢复并继续运行程序。

# “断言”进化史

## “石器时代”

一开始的一些单元测试框架（比如JUnit）提供的断言语句，这样在程序某个地方确保某个逻辑关系肯定返回是true,如果不是true,这个单元测试就是没有测试通过。如下就是一个例子,如果程序运行到此行时返回false程序就会抛出一个错误（如下图一）并停止运行，开发人员可以去检查下为什么出现此问题。非常的简单粗爆。

```java
assert(x=y);
```

![](http://cloudsdocker.github.io/images/blog_assert_1.png)

## “青铜时代”

上面这种断言除了简单之外，是有一个问题，就是当断言被触发时显示出来的错误消息不是很友好。如上图一，只是知道出错了，但是并没有太多有用的信息，比如最好是能显示出x与y的值来，这样好更快的理解为啥出错。后来，支持断言的单元测试框架升级版本出现了，它们提供了一系列的高级”断言“语句，添加了一些更加友好的程序接口，同时还提供比较亲民的错误消息，比如下面的例子使用了两个单独的断言语句。

```java
int x=111;
int y=222;      
assertEquals(x, y);
assertNotEquals(x, y);
```

执行的结果如下图二，你可以看到这个错误结果相对于上面“石器时代”已经包括了不少有用的信息，比如除了知道断言失败外还显示了`期望的值`以及`实际值`。

![](http://cloudsdocker.github.io/images/blog_assert_2.jpg)

## “黄金时代”

但是上面这种方式有一个弊端，就是需要大量的预置断言方法（比如判断相等一个方法，判断不相等一个方法等），去支持各种场景。接下来又出现了新的解决方案，其中的明星就是`Hamcrest` (其实这个词是使用一种叫做[angram](https://en.wikipedia.org/wiki/Anagram)的文字游戏，即把一个原来单词中的字母顺序改变，这个Hamcrest就是从Matchers的变形)框架。是使用一种`assertThat`组合上`Matcher`来使用。

这个有多个好处， 
- 首先是支持了在Java8中才迟迟引入的`流式编程(Stream)`，即每个Matcher执行完后会再返回一个Matcher，这样可以一个套一个组成一个Matcher链
- 另外Hamcrest还使用了非常接近于人类自然语言以及使用and/or/not等逻辑判断的方式来写测试方法，比如当你看到下面的测试语句肯定会一目了然：

```java
assertThat(actual, is(not(equalTo(expected)));
```

- 还有一个好处是输出的断言消息更加易读。
- 另外还有一个好处即Hamcrest框架支持泛型`TypeSafe`，即在编译时就会找到类型不匹配的错误。比如下面第一个是传统的断言，在编译期不会报错，但是运行时会失败，而第二个会在编译时报错，就不用等到运行期。

```java
assertEquals("abc", 123); // 1
assertThat(123, is("abc")); // 2
```

![](http://cloudsdocker.github.io/images/blog_assert_3.jpg)

- 使用Hamcrest的最后一个好处是对测试框架的“解耦合”，即，使用此框架你可以现在使用Junit后面可以转到TestNG。甚至你自己去扩展自己实现。

# 总结

上面说了这么多，是不是感觉平时经常使用的一个看似简简单单的Assert还有不少的东西可以深挖一下滴。这个只是抛砖引玉，如果大家还有什么点子或建议请使用下面的方式。

> 联系我：
* phray.zhang@gmail.com (email/邮件，whatsapp, linkedin)
* helloworld_2000 (wechat/微信)
* [blog on github pages](http://cloudsdocker.github.io)
* [简书 jianshu](http://www.jianshu.com/users/a9e7b971aafc/latest_articles)
* [github](https://github.com/CloudsDocker/)
* 微信公众号：vibex

### Reference:

- [benefit of assertThat](https://objectpartners.com/2013/09/18/the-benefits-of-using-assertthat-over-other-assert-methods-in-unit-tests/)

