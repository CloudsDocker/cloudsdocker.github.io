---
header:
    image: /assets/images/hd_java_deep_notes.png
date: 2022-02-09
title: Java Deep Notes
tags:
- Java
layout: single
category: tech
---
Java Deep Notes

# How to avoid NPE null in middle of Java Lambda
The key is add a step `.filter(Objects::nonNull)`
Here is a usage sample:

```java
dataMap.keySet().stream()
                .map(discountMapping::get)
                .filter(Objects::nonNull)
                .map(it -> it.applyDiscount(this))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
```

# Is string concatenation a devil?

In fact, a string concatenation is going to be just fine, as the javac compiler will optimize the string concatenation as a series of append operations on a StringBuilder anyway. Here's a part of the disassembly of the bytecode from the for loop from the above program:


