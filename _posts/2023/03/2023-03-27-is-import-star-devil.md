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

 - Intentionality: When you import classes individually, it demonstrates that you have a clear understanding of the dependencies in your code. This intentionality can help you write more purposeful code and reduce the likelihood of introducing unintended dependencies or bugs.

 - Easier navigation in IDEs: Most modern integrated development environments (IDEs) provide features for navigating between classes and automatically managing imports. By importing classes individually, you can more easily navigate between classes and quickly locate the class definitions or usage.

 - Easier refactoring: If you need to refactor your code or switch to a different library with similar functionality, having individual imports makes it easier to identify which classes are being used, making the refactoring process smoother.

 - Minimizing the chance of accidental usage: Wildcard imports can lead to the accidental usage of classes that you didn't intend to use. This can happen if you mistakenly use a class with a similar name from the imported package or if a new class is added to the package in the future. Importing classes individually helps to prevent these issues.

 - Better version control: When you import classes individually, it becomes easier to track changes in version control systems like Git. When a new import is added or removed, it's clear which specific class was added or removed, making it simpler to understand the impact of changes in the code.

 - Compliance with coding standards: Many organizations and open-source projects have coding standards that recommend importing classes individually to improve code quality and maintainability. Following these guidelines can help you contribute to these projects more effectively and make your code more consistent with best practices.


In summary, it's generally better to import classes individually in Java. Wildcard imports can have negative impacts on code readability, maintainability, and compiler optimizations.

--HTH--
