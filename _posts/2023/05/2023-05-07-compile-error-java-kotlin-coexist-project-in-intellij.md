---
title: Compile Error Java Kotlin Coexist Project In Intellij
header:
    image: /assets/images/let-AI-to-manage-stripe-payment.jpg
date: 2023-05-07
tags:
- Java
- Intellij
- Coding

permalink: /blogs/tech/en/compile-error-java-kotlin-coexist-project-in-intellij
layout: single
category: tech
---
> The biggest room in the world is the room for improvement.
— Helmut Schmidt

# How to Fix Compile Error for a Mixed Java and Kotlin Project

If you're having trouble compiling a project that contains both Java and Kotlin classes, and the Kotlin classes are not being compiled, there are several steps you can take to resolve the issue.

## 1. Check for the Kotlin Plugin

First, check to make sure that the Kotlin plugin is installed in your IDE or build system. If you're using an IDE like Android Studio or IntelliJ IDEA, ensure that the Kotlin plugin is installed and enabled. If you're using a build system like Gradle, make sure that the Kotlin plugin is added to your project's dependencies.

## 2. Verify the Kotlin File Location

Next, ensure that your Kotlin files are located in the proper directory. By default, Kotlin files should be located in the `src/main/kotlin` directory. Ensure that your Kotlin files are in this directory, as the build system may not recognize them otherwise.

## 3. Check for Syntax Errors

If there are any syntax errors in your Kotlin files, the build system may not be able to compile them. Check for any errors or warnings in your Kotlin files and correct them.

## 4. Verify the Kotlin Version

Make sure that the correct version of Kotlin is specified in your project's build files. If the version of Kotlin is not specified, the build system may not be able to compile the Kotlin classes.

## 5. Clean and Rebuild Your Project

Sometimes, a simple clean and rebuild of your project can resolve any issues with compiling Kotlin classes. Clean your project by running `./gradlew clean` or `./gradlew cleanBuildCache` (if using Gradle) and then rebuild your project. This will force the build system to recompile all the classes, including the Kotlin classes.

If none of these steps resolve the issue, there may be a more complex issue with your project's configuration. In that case, you may need to consult the documentation for your IDE or build system or seek assistance from a developer with expertise in Kotlin and Java mixed projects.

# Lastly and Most Importantly killer solution

## Restart your laptop
## Then run above maven build should solve the problem (hopefully)

```shell
mvn clean install -DskipTests -T1C -e
```

Thank you for reading, and happy coding!

--HTH--
