---
title: Java Deep Notes
tags:
- Java
layout: posts
---
Java Deep Notes

# Is string concatenation a devil?

In fact, a string concatenation is going to be just fine, as the javac compiler will optimize the string concatenation as a series of append operations on a StringBuilder anyway. Here's a part of the disassembly of the bytecode from the for loop from the above program:


