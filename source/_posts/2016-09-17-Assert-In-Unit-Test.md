---
title: 浅谈软件单元测试中的“断言” (assert)
tag:
- java
- testing
---

大家都知道，在软件测试，特别是在单元测试时肯定会用到的一个功能就是“断言”，最近在偶然的机会想到此功能，在此整理一下之前使用以及对“断言”的理解。

# 什么是断言
程序员在开发程序中预计在程序运行到某个节点位置，某些逻辑条件必须满足，否则程序就要"报错"甚至是"崩溃"。

# “断言” vs “异常， 即 Assert vs. Exception


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

