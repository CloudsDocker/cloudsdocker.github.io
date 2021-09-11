---
title: Data Structure
tags:
 - programming
 - data strucutre
layout: posts
---

# Binary Tree
- A binary tree is a tree in which no node can have more than two children.
- A property of a binary tree that is sometimes important is that the depth of an average
binary tree is considerably smaller than N. An analysis shows that the average depth is √O( N), and that for a special type of binary tree, namely the binary search tree, the average value of the depth is O(log N). Unfortunately, the depth can be as large as N − 1, 

# Cyclic List
## Round Robin scheduling
- using some form of an algorithm known as round-robin scheduling. A process is given a short turn to execute, known as a time slice, but it is interrupted when the slice ends, even if its job is not yet complete.

# doubly linked list
- a doubly linked list. These lists allow a greater variety of O(1)-time update operations, including insertions and deletions at arbitrary posi- tions within the list. 
- Header and Trailer Sentinels
- a header node at the beginning of the list, and a trailer node at the end of the list. These “dummy” nodes are known as **sentinels** (or guards), and they do not store elements of the primary sequence. 

## Advantages using sentinel
- Although we could implement a doubly linked list without sentinel nodes (as we did with our singly linked list in Section 3.2), the slight extra memory devoted to the sentinels greatly simplifies the logic of our operations. Most notably, the header and trailer nodes never change—only the nodes between them change. Furthermore, we can treat all insertions in a unified manner, because a new node will always be placed between a pair of existing nodes. In similar fashion, every element that is to be deleted is guaranteed to be stored in a node that has neighbors on each side.

# Equivalence relation
equivalence relation in mathematics, satisfying the following properties:
- Treatment of null: For any nonnull reference variable x, the call x.equals(null) should return false (that is, nothing equals null except null).
- Reflexivity: Foranynonnullreferencevariablex,thecallx.equals(x)should return true (that is, an object should equal itself).
- Symmetry: For any non null reference variables x and y,the calls x.equals(y) and y.equals(x) should return the same value.
- Transitivity: For any nonnull reference variables x, y, and z, if both calls x.equals(y) and y.equals(z) return true, then call x.equals(z) must return true as well.

## Ring Buffer
In other words, the circular buffer is well-suited as a FIFO buffer while a standard, non-circular buffer is well suited as a LIFO buffer.
Circular buffering makes a good implementation strategy for a queue that has fixed maximum size. Ref to [this wiki page](https://en.wikipedia.org/wiki/Circular_buffer)

