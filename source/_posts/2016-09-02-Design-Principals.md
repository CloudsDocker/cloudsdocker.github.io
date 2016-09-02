---
title: 漫谈开发设计中的一些‘原则’
tags:
- development
- desgin
- principals
---

在开发设计中有一些常用原则或者潜规则，根据笔者的经验，这里稍微总结一下，以飨读者。

# DRY 
这里的DRY是Do Not Repeat Yourself的缩写。具体解释参见 [wiki](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself),严谨的定义是　Every piece of knowledge must have a single, unambiguous, authoritative representation within a system，意思是：任何一部分知识在系统中必须只有单一的，清晰并且权威的展示。？？？这是啥意思，没懂。简单说就是不要重复自己任何一部分的工作。比如说，有一段代码是用于清除字条串中的多余的空格，在多个程序中会用到此功能，如果每个地方都使用
