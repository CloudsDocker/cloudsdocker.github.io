---
title: 浅谈软件单元测试中的“断言” (assert)
tag:
- java
- testing
---

大家都知道，在软件测试，特别是在单元测试时肯定会用到的一个功能就是“断言”，最近在偶然的机会想到此功能，在此整理一下之前使用以及对“断言”的理解。比如你知道“断言”的发展一路过来的心路历程吗？

# 什么是断言
程序员在开发程序中预计在程序运行到某个节点位置，某些逻辑条件必须满足，如果不满足，程序就会"报错"甚至是"崩溃"。这样程序开发人员就可以在第一时间知道这个问题，而非等到交付给用户后才发现问题。这个功能是TDD (Test Driven Develop)的基石之一。

# “断言” vs "异常"或者错误， 即 Assert vs. Exception/Error
- “断言”通常是给程序开发人员自己使用，并且在开发期间使用。而异常等在程序运行期间触发
- 通常“断言”触发后程序“崩溃”退出，不需要从错误中恢复。而“异常”通常会使用try/catch等结构从错误中恢复并继续运行程序。

# “断言”的历史

## 断言的“石器时代”

此时一些单元测试框架提供断言语句，这样在程序某个地方确保某个逻辑关系肯定返回是true,如果不是true,这个单元测试就是没有测试通过。如下是这样的一个例子：
"First generation" unit test frameworks provide an 'assert' statement, allowing one to assert during a test that a particular condition must be true. If the condition is false, the test fails. For example:
```java
assert(x == y);
```
But this syntax fails to produce a sufficiently good error message if 'x' and 'y' are not equal. It would be better if the error message displayed the value of 'x' and 'y'. To solve this problem, "second generation" unit test frameworks provide a family of assertion statements, which produce better error messages. For example,
```java
assert_equal(x, y);
assert_not_equal(x, y);
```
But this leads to an explosion in the number of assertion macros, as the above set is expanded to support comparisons different from simple equality. So "third generation" unit test frameworks use a library such as Hamcrest to support an 'assert_that' operator that can be combined with 'matcher' objects, leading to syntax like this:

```java
assert_that(x, equal_to(y))
assert_that(x, is_not(equal_to(y)))
```

The benefit is that you still get fluent error messages when the assertion fails, but now you have greater extensibility. It is now possible to define operations that take matchers as arguments and return them as results, leading to a grammar that can generate a huge number of possible matcher expressions from a small number of primitive matchers.

These higher-order matcher operations include logical connectives (and, or and not), and operations for iterating over collections. This results in a rich matcher language which allows complex assertions over collections to be written in a declarative, rather than a procedural, programming style.


# Reference
