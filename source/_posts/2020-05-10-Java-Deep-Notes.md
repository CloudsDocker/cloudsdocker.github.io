---
title: Java Deep Notes
tags:
- Java
---
Java Deep Notes

# Is string concatenation a devil?

In fact, a string concatenation is going to be just fine, as the javac compiler will optimize the string concatenation as a series of append operations on a StringBuilder anyway. Here's a part of the disassembly of the bytecode from the for loop from the above program:

# To avoid start a new thread
It's nothing wront with creating a thread in a constructor, but it's best not to `start` the thread immediately. Instead, expose a strat or initialize method that starts the owned thread.
This is because when an object creats a thread from its contructor, it almost alwasy shares its `this` reference with the new therd., either explicitiely (by passing it to the constructor) or implicitly (becuase the Thread or Runable is an inner class of the owning object). The new thread might then be able to see the owning object before it is fully contructed. That will lead to some reading of `stale` data/state and concurrency issues.