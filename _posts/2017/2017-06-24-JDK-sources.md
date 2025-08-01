---
layout: posts
title: JDK source
tags:
- java
---

# interface RandomAccess
Marker interface used by List implementations to indicate that they support fast (generally constant time) random access. The primary purpose of this interface is to allow generic algorithms to alter their behavior to provide good performance when applied to either random or sequential access lists.


 Such a List implementation should generally implement this interface. As a rule of thumb, a List implementation should implement this interface if, for typical instances of the class, this loop:
 
 ```java
       for (int i=0, n=list.size(); i < n; i++)
           list.get(i);
   
// runs faster than this loop:
       for (Iterator i=list.iterator(); i.hasNext(); )
           i.next();


```
