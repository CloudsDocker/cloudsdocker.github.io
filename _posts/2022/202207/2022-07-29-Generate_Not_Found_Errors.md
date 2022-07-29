---
header:
    image: /assets/images/hd_cannot_find_symbol_generated.jpg
title:  Cannot find symbol class Generated or var
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

## Error 1: Cannot find symbol class Generated
If you are using some libraries to generate source code, such as `MapStruct`, `QueryDSL`,some annotation wil be processed and those java classed java sources will be saved under `target` folder.

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


# Error 2: cannot find symbol class var

If you are using new Java keyword `var` and combiled good, however get following error in runtime;

> java: as of release 10, 'var' is a restricted local variable type and cannot be used for type declarations or as the element type of an array

The error may look like below:
![](/assets/images/error_var_java_10.jpg)

You may think this is an easy fix and try to update JDK version in maven pom.xml, unfortuantely it may not work. 

## Solution

If you spot in more details you may realized this is *compile* good but failed in *run*. As you know, Java will compile to *byte code* and JVM will use the *byte code* to spin up a new Java process. So the error should fall in the byte code.

This can be fixed by updating following config in your IDE:

### go to Build->Compiler->Java Compiler-> Target bytecode version

![](/assets/images/java_byte_code_fix_intelliJ.jpg)




--HTH--



