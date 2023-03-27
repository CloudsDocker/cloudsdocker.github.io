---
title: Is-import-star-devil.md
header:
    image: /assets/images/spring-hibernate-transaction-errors-deep-dive.jpg
date: 2023-03-26
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/is-import-star-devil
layout: single
category: tech
---

# Why using wildcard import is devil

Using import * (also known as a wildcard import) in Java is generally not recommended, especially in larger projects or when working with multiple libraries. Instead, it is better to import classes individually. Here's why:

 - Readability: When you import classes individually, it is easier to understand which classes are being used in your code. This makes it more readable and easier for others to understand and maintain.

 - Avoiding name conflicts: Importing classes individually can help you avoid name conflicts between classes with the same name from different packages. If you use wildcard imports and encounter a name conflict, you'll need to use the fully-qualified class name, which can be cumbersome.

 - Code maintainability: As your project grows, it may become challenging to keep track of all the imported classes if you're using wildcard imports. Importing classes individually makes it easier to identify unused imports and remove them, reducing the chance of errors and improving code maintainability.

 - Compiler optimization: When you import classes individually, the compiler can optimize your code better. Wildcard imports can result in slower compilation times and larger bytecode, as the compiler needs to resolve the imported classes.

In summary, it's generally better to import classes individually in Java. Wildcard imports can have negative impacts on code readability, maintainability, and compiler optimizations.

--HTH--
