---
header:
    image: /assets/images/what-is-default-logic-in-python-try-except-else.jpg
title: What is default logic in python try except else
date: 2023-02-18
tags:
 - Python
 
permalink: /blogs/tech/en/what-is-default-logic-in-python-try-except-else
layout: single
category: tech
---

> Keep an eye on the fruits of your labor.

# What is default logic in python try except else
in python, In the try-except-else block, when will the else part be executed?

In Python, the try-except-else block is used to handle exceptions that might occur in the try block of code. The basic syntax of the try-except-else block is as follows:

```python

try:
    # code that might raise an exception
except ExceptionType:
    # code to handle the exception
else:
    # code to run if no exception was raised
```
The else block is executed only if no exception is raised in the try block. If an exception is raised, the except block is executed, and the else block is skipped.

In other words, if the code in the try block executes successfully without raising any exceptions, then the code in the else block will be executed. If an exception is raised in the try block, the code in the except block will be executed and the else block will be skipped.

The else block is optional and can be omitted if it is not required in the code.
--HTH--



