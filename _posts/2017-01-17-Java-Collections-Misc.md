---
layout: posts
title: Java Collections Misc
tags:
- java
- Collections
---
# Difference between equals and deepEquals of Arrays in Java
- Arrays.equals() method does not compare recursively if an array contains another array 
- on other hand Arrays.deepEquals() method compare recursively if an array contains another array. 
- Arrays.equals() check is if element is null or not and then calls equals() method, it does not check for Array type. 
- It's better to use **Arrays.equals()** to compare **non-nested** Array and Arrays.**deepEquals() to compare nested Array**, as former is faster than later in the case of non-nested Array.

# Checking Array for duplicate elements Java
1. **brute force** method which compares each element of Array to all other elements and returns true if it founds duplicates. Though this is not an efficient choice it is the one which first comes to mind. complexity on order of O(n^2) not advised in production
1. Another quick way of checking if a Java array contains duplicates or not is to **convert that array into Set**. Since Set doesn’t allow duplicates size of  the corresponding Set will be smaller than original Array if Array contains duplicates otherwise the size of both Array and Set will be same. 
```java
 List inputList = Arrays.asList(input);
 Set inputSet = new HashSet(inputList);
```
1. One more way to detect duplication in java array is adding every element of the **array into HashSet** which is a Set implementation. Since the add(Object obj) method of Set returns false if Set already contains an element to be added, it can be used to find out if the array contains duplicates in Java or not.

- If you don't prefer converting List to Set than you can still go with copying data **from one ArrayList to other ArrayList ** and removing duplicates **by checking with ArrayList.contains()** method.
# List vs Set
In short main difference between List and Set in Java is that List is an **ordered** collection which **allows duplicates** while **Set is an unordered** collection which **doesn't allow duplicates**.

# how to sort list in reverse order
- Collections.sort(unsortedList, Collections.reverseOrder());
- customized comparator
- Collections.sort(unsortedList, String.CASE_INSENSITIVE_ORDER); // search insensitive order

# Find length of a linked list

## Iterative Solutions
```java
public int length(){
 int count=0;
 Node current = this.head;

 while(current != null){
  count++;
  current=current.next()
 }
 return count;
}
```

## Recursive Solution:
```java
public int length(Node current){
 if(current == null){ //base case
   return 0;
 }
 return 1+length(current.next());
}
```

You can see that we have used the fact that last node will point to null to terminate the recursion. This is called the **base case**. It's very important to identify a base case while coding a recursive solution, without a base case, your program will never terminate and result in StackOverFlowError.


# Iterator 
- is nothing but a traversing object, made specifically for Collection objects like List and Set. 
- we have already aware about different kind of traversing methods like for-loop ,while loop,do-while,for each lop etc,they all are  index based traversing but as we know Java is purely object oriented language there is always possible ways of doing things **using objects so Iterator is a way to traverse as well as access the data from the collection**. 

# ListIterator
- in Java is an Iterator which allows user to traverse Collection like ArrayList and HashSet in both direction by using method **previous() and next ()**. You can obtain ListIterator from all List implementation **including ArrayList and LinkedList**. ListIterator doesn’t keep current index and its current position is determined by call to next() or previous() based on direction of traversing.
 - List collection type also supports ListIterator which has add() method to add elements** in collection while Iterating. 

# Blocking queue
- BlockingQueue in Java doesn't allow null elements, various implementation of BlockingQueue like ArrayBlockingQueue, LinkedBlockingQueue throws NullPointerException when you try to add null on queue.
## BlockingQueue can be bounded or unbounded. 
- A **bounded** BlockingQueue is one which is **initialized with initial capacity** and call to **put() will be blocked** if BlockingQueue is full and size is equal to capacity. This bounding nature makes it **ideal to use a shared queue between multiple threads** like in most common Producer consumer solutions in Java. 
- An **unbounded Queue** is one which is **initialized without capacity**, actually by default it initialized with Integer.MAX_VALUE. most common example of BlockingQueue uses bounded BlockingQueue as shown in below example.
```java
BlockingQueue<String> bQueue = new ArrayBlockingQueue<String>(2);
```
## BlockingQueue implementations like ArrayBlockingQueue, LinkedBlockingQueue and PriorityBlockingQueue are **thread-safe**. 
- All queuing method uses concurrency control and internal locks to perform operation atomically. 

## BlockingQueue interface extends Collection, Queue and Iterable interface which provides it all Collection and Queue related methods like **poll(), and peak()**, unlike take(), **peek()** method returns head of the queue **without removing it**, **poll() also retrieves and removes elements from head but can wait till specified time if Queue is empty**.



 
# Reference
- http://javarevisited.blogspot.com/2012/12/how-to-compare-arrays-in-java-equals-deepequals-primitive-object.html#ixzz4WBifkyjg
- http://javarevisited.blogspot.in/2012/02/how-to-check-or-detect-duplicate.html
- http://javarevisited.blogspot.com/2012/12/how-to-remove-duplicates-elements-from-ArrayList-Java.html#ixzz4WBkudSwR
- http://javarevisited.blogspot.in/2012/04/difference-between-list-and-set-in-java.html
- http://javarevisited.blogspot.in/2012/01/how-to-sort-arraylist-in-java-example.html
- http://javarevisited.blogspot.in/2016/05/how-do-you-find-length-of-singly-linked.html
- http://javarevisited.blogspot.in/2011/10/java-iterator-tutorial-example-list.html
- http://javarevisited.blogspot.in/2012/12/blocking-queue-in-java-example-ArrayBlockingQueue-LinkedBlockingQueue.html
