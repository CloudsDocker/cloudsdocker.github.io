---
title: Understanding Python's Late Binding Behavior  A Deep Dive
header:
    image: /assets/images/Understanding_Python_s_Late_Binding_Behavior__A_Deep_Dive.jpg
date: 2023-07-09
tags:
- Python
- Algorithm
- Coding

permalink: /blogs/tech/en/Understanding_Python_s_Late_Binding_Behavior__A_Deep_Dive
layout: single
category: tech
---
> "Hang Out with People Who are Better than You."
>— Warren Buffett

# Understanding Python's Late Binding Behavior: A Deep Dive

In the world of Python, understanding the nuances of how variables and functions interact can sometimes be a challenge. Let's take a closer look at one such concept: Python's late binding behavior and its effects when dealing with lambda functions in a loop.

## The Code
```python
python
Copy code
functions = []
for i in range(10):
functions.append(lambda: i)

for f in functions:
print(f())
```
At first glance, you might expect this code to print out the numbers 0 through 9. However, the actual output is quite different.

## The Output
Believe it or not, this code will print the number 9 ten times! So, why does this happen? The answer lies in how Python handles late binding.

## Python's Late Binding Behavior
The range(10) in the loop will iterate over the numbers 0 through 9. For each number, the code creates a lambda function lambda: i, which should return the current value of i. This lambda function is then appended to the functions list.

Here's the catch: The lambda function doesn't capture the value of i at the time the function is created. Instead, it captures the variable i itself. This means that when the lambda function is later called, it will return the current value of i, not the value i had when the function was created.

By the time we reach the second loop, i is equal to the final value from the previous loop, which is 9 (as range(10) generates values from 0 to 9). So each call to f() will print 9.

## A Better Approach
If you want each function to remember the value of i at the time it was created, you can provide that value as a default argument to the lambda function. This will effectively "capture" the value at the time of the lambda function's creation. Here's how you can modify the code to achieve this:

```python
functions=[]
for i in range(10):
functions.append(lambda i=i: i)

for f in functions:
print(f())
```
With this modification, the code now prints out the numbers 0 through 9, as one might initially expect. Each lambda function now captures the value of i at the time it was created.

## Wrap Up
This is a perfect example of why it's so important to understand the nuances of the programming languages we use. Knowing about Python's late binding behavior can help you avoid unexpected results when working with loops and lambda functions. Keep exploring, and happy coding!

-HTH-