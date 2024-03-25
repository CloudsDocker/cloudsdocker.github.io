---
title: IntelliJ sudden crashed of compile error MapStruct or Kotlin
header:
    image: /assets/images/BangkokCircle_ROW8678634220_UHD.jpeg
date: 2024-03-25
tags:
- Java
- Programming
- IntelliJ

permalink: /blogs/tech/en/intellij-sudden-crashed-of-compile-error-mapstruct
layout: single
category: tech
---
> Life begins at the edge of the comfort zone

# Intellij Sometimes crash compiling some error such auto generated MapStruct class not found or Kotlin class not found

This is may be because of the IntelliJ cache, so you can try to invalidate the cache and restart the IntelliJ.

# Solution - 1

## Here are sample screenshots of the error:

![img.png](/assets/images/2024/03/25/img.png)

The simplest way to do this is to click on the File menu and select the Invalidate Caches / Restart option. This will bring up a dialog box with the option to invalidate the caches, restart the IDE, or both. Click on the Invalidate and Restart button to clear the cache and restart IntelliJ IDEA.

## Here is the second screenshot of the fixing process:
![img.png](/assets/images/2024/03/25/img_1.png)

# Solution - 2
When previous step not working you can try 
- Close the IntelliJ for **all** projects, in MacBooks you can do this by pressing `Command + Q`
- Restart the IntelliJ with your project
- Rebuild the project by pressing `Command + F9`

# Solution - 3
When previous step not working you can try to use the terminal to clean the cache by running the following command:
```shell
rm -rf ~/Library/Caches/JetBrains/IntelliJIdea2021.3
```
Then build the project in external terminal by running the following command:
```shell
mvn clean install -T1C -DskipTests
``` 

--HTH--