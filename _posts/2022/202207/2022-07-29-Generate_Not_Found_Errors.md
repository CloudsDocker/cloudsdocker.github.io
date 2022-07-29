---
header:
    image: /assets/images/hd_cannot_find_symbol_generated.jpg
title:  Cannot find symbol clas Generated
date: 2022-07-29
tags:
 - Java
 - Intellij
 
permalink: /blogs/tech/en/cannot_found_symbol_generated
layout: single
category: tech
---

> The best way to predict the future is to create it.

# Summary

# What's the error

If you are using some libraries to generate source code, such as `MasStruct`, `QueryDSL`,some annotation wil be processed and those java classed java sources will be saved under `target` folder.

However, if you getting errors in thsoe generated class, such as `cannot find symbol calss Generated`, this is acatualy one class in javax.annotation.processing package.

here is the error screenshot:
![](/assets/images/generated_not_found_errors.jpg)



# Solution

Firslty you may be tempted to add one dependency in maven, like below one 

```
<dependency>
    <groupId>javax.annotation</groupId>
    <artifactId>javax.annotation-api</artifactId>
    <version>1.3.2</version>
</dependency>
```

Generally this should not work (but if it do to you, congradulations and you can close this page now. :-) )

If not, let's keep reading. 

The root cause is actaully this `Generated` is introduced from JDK 9. So you need to make sure your project is using JDK 9+. 

So go to check your pom.xml (maven) to make sure no JDK 8 but at lease 9, such as below example:


![](/assets/images/generated_error_pom_jdk.jpg)




--HTH--



