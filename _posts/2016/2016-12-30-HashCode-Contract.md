---
layout: posts
title: Hash Code Misc
tags:
- java
- hashcode
---

# contract of hashCode :
- Whenever it is **invoked on the same object more than once during an execution of a Java application, the hashCode method must consistently return the same integer**, provided no information used in equals comparisons on the object is modified. This _integer need **not** remain consistent from one execution of an application to another execution of the **same** application_.
- If two objects **are equal** according to the equals(Object) method, then calling the hashCode method on each of the two objects must produce the **same integer** result.
- It is **not required** that **if two objects are unequal** according to the equals(java.lang.Object) method, then calling the hashCode method on each of the two objects **must produce distinct integer results**. However, the programmer should be aware that producing distinct integer results for unequal objects _may improve the performance of hash tables_.

As much as is reasonably practical, the hashCode method defined by class Object does return distinct integers for distinct objects. (This is typically implemented by **converting the internal address** of the object into an integer, but this implementation technique is not required by the JavaTM programming language.)

# Hashcode in Java Collections
## Hashcode vs. equals
### Equals
For usage in java collections framework, **equals()** used in following scenarios:
- contains or not
- to remove one item

Below is one implementation of a Equals
```java
public class Employee{
    public boolean equals(Object o){
        if(o==null) return false;
        if(!(o instanceof Employee)) return false;

        Employee other=(Employee)o;
        return this.employeeID==other.employeeID;
    }
}
```

### Hashcode
When insert data into HashTable, HashMap, HashSet, the hashcode used to determine **where** to **store/search** the value in list/bucket. The hashcode only **point to an area** in list/bucket of data. The hashtable then iterates this area (all keys with the same hash code) and uses the key's equals() method to find the right key. Once the right key is found, the object stored for that key is returned. 

After you override the hashcode, you are still be able to get origional hashcode via calling **int originalHashCode = System.identityHashCode(emp1);**

### Rules
In this regard there is a rule of thumb that if you are going to overide the one of the methods (equals, hashcode), you have to override both, othersise it's a violation of contract .


## HashMap tips
- Since searching inlined list is O(n) operation, in worst case hash collision reduce a map to linked list. This issue is recently addressed in Java 8 by replacing linked list to the tree to search in O(logN)
- **HashMap works on the principle of hashing**.
-  HashMap  stores both Key and Value in LinkedList node or as Map
- using immutable, final object with proper equals() and hashcode() implementation would act as perfect Java HashMap  keys and improve the performance of Java HashMap  by reducing collision. **Immutability also allows caching their hashcode of different keys which makes overall retrieval process very fast** and suggest that String and various wrapper classes e.g. Integer very good keys in Java HashMap.
- if the load factor is .75 it will act to re-size the map once it filled 75%. Java HashMap re-size itself by creating a new bucket array of size twice of the previous size of HashMap and then start putting every old element into that new bucket array. This process is called rehashing because it also applies the hash function to find new bucket location. 
- there is potential race condition exists while resizing HashMap in Java, if two thread at the same time found that now HashMap needs resizing and they both try to resizing. on the process of resizing of HashMap in Java, the element in the bucket which is stored in linked list get reversed in order during their migration to new bucket because Java HashMap  doesn't append the new element at tail instead it append new element at the head to avoid tail traversing.
- If race condition happens then you will end up with an infinite loop. 


## Why String, Integer and other wrapper classes are considered good keys?

- String, Integer and other wrapper classes are natural candidates of HashMap key, and String is most frequently used key as well because String is immutable and final, and overrides equals and hashcode() method. 
- Immutability is best as it offers other advantages as well like thread-safety, If you can  keep your hashCode same by only making certain fields final, then you go for that as well.

# ConcurrentHashMap
- ConcurrentHashMap provides better concurrency by only locking portion of map determined by concurrency level. 
- but Hashtable provides stronger thread-safety than ConcurrentHashMap
- ConcurrentHashMap performs better than earlier two because it only locks a portion of Map, instead of whole Map, which is the case with Hashtable and synchronized Map. 
- provided all functions supported by Hashtable with an additional feature called "concurrency level", which allows ConcurrentHashMap to partition Map.
- ConcurrentHashMap allows multiple readers to read concurrently without any blocking. This is achieved by partitioning Map into different parts based on concurrency level and locking only a portion of Map during updates. 
- **Default concurrency level is 16**, and accordingly Map is divided into 16 part and each part is governed with a different lock. This means, 16 thread can operate on Map simultaneously until they are operating on different part of Map. 
-  Since update operations like put(), remove(), putAll() or clear() is not synchronized, concurrent retrieval may not reflect most recent change on Map.
- ConcurrentHashMap also uses ReentrantLock to internally lock its segments.
- In hashmap and hashtable, you can check one item first and add it if not present. Though this code will work fine in HashMap and Hashtable, This won't work in ConcurrentHashMap; because, during put operation whole map is not locked, and while one thread is putting value, other thread's get() call can still return null which result in one thread overriding value inserted by other thread. Ofcourse, you can wrap whole code in synchronized block and make it thread-safe but that will only make your code single threaded. ConcurrentHashMap provides putIfAbsent(key, value) which does same thing but atomically and thus eliminates above race condition
- ConcurrentHashMap is best suited when you have **multiple readers** and **few writers**. If writers outnumber reader, or writer is equal to reader, than performance of ConcurrentHashMap **effectively reduces to synchronized map or Hashtable**. Performance of CHM drops, because you got to **lock all portion of Map**, and effectively each reader will wait for another writer, operating on that portion of Map. ConcurrentHashMap is a good choice for caches, which can be initialized during application start up and later accessed my many request processing threads.
- ConcurrentHashMap allows **concurrent read** and **thread-safe update** operation.
- Iterator returned by ConcurrentHashMap is weekly consistent, fail-safe and never throw ConcurrentModificationException. 
- In Java.ConcurrentHashMap **doesn't allow null as key or value**.

# How null work in HashMap
 How null key is handled in HashMap? Since equals() and hashCode() are used to store and retrieve values, how does it work in case of the null key?

The null key is handled specially in HashMap, there are two separate methods for that putForNullKey(V value)
and getForNullKey()
. Later is offloaded version of get() to look up null keys.  Null keys always map to index 0.  This null case is split out into separate methods for the sake of performance in the two most commonly used operations (get and put), but incorporated with conditionals in others. In short, equals()
and hashcode() method are not used in case of null keys in HashMap.

# Performance changes in JDK 1.7 and 1.8
- There is some performance improvement done on HashMap and ArrayList from JDK 1.7, which reduce memory consumption. Due to this empty Map are lazily initialized and will cost you less memory. Earlier, when you create HashMap e.g. new HashMap() it automatically creates an array of default length e.g. 16. After some research, Java team found that most of this Map are temporary and never use that many elements, and only end up wasting memory. Also, From JDK 1.8 onwards HashMap has introduced an improved strategy to deal with high collision rate. Since a poor hash function e.g. which always return location of same bucket, can turn a HashMap into linked list, i.e. converting get() method to perform **in O(n) instead of O(1)** and someone can take advantage of this fact, Java now internally replace linked list to a binary true once certain threshold is breached. This ensures performance or order O(log(n)) even in the worst case where a hash function is not distributing keys properly.
- such change is creating empty ArrayList and HashMap with size zero in JDK 1.7.0_40 update.
-  If you are running on Java 1.6 or earlier version of Java 1.7, you can open code of java.util.ArrayList and check that, currently empty ArrayList is initialized with Object array of **size 10**. If you create several temporary list in your program, which remains uninitialized, due to any reason then you are not only losing memory but also losing performance by giving your garbage collector more work.
- Same is true for empty HashMap, which was initialized by **default initial capacity of 16**. This changes are result of observation made by Nathan Reynolds, and Architect at Oracle, which apparently analysed 670 Java heap dumps from different Java programs to find out memory hogs.
-  By the way, it's not just memory, it’s also extra work-load for Garbage collector

# Hashtable
- One of the major differences between HashMap and Hashtable is that HashMap is non-synchronized whereas Hashtable is synchronized
- Another difference is HashMap allows **one** null key and null values but **Hashtable doesn't allow null ** key or values.
- Another significant difference between HashMap vs Hashtable is that Iterator in the **HashMap is  a fail-fast ** iterator  while the enumerator for the **Hashtable is not and throw ConcurrentModificationException** if any other Thread modifies the map structurally  by adding or removing any element except Iterator's own remove() method


# ConcurrentHashMap vs Hashtable vs Synchronized Map
- Though all three collection classes are thread-safe and can be used in multi-threaded, concurrent Java application, there is a significant difference between them, which arise from the fact that **how they achieve their thread-safety**. 
- Hashtable is a legacy class from JDK 1.1 itself, which uses **synchronized methods** to achieve thread-safety. All methods of Hashtable are synchronized which makes them quite slow due to contention if a number of thread increases. 
- Synchronized Map is also **not very different than Hashtable** and provides similar performance in concurrent Java programs. The only difference between Hashtable and Synchronized Map is that later is not a legacy and you **can wrap any Map** to create it's synchronized version by using Collections.synchronizedMap()
- Unlike Hashtable and Synchronized Map, it **never locks whole Map**, instead, it divides the map into segments and locking is done on those. Though it performs better if a number of **reader threads are greater than** the number of writer threads.
- **ConcurrentHashMap and CopyOnWriteArrayList** implementations provide much **higher concurrency while preserving thread safety**, with some minor compromises in their promises to callers. ConcurrentHashMap and CopyOnWriteArrayList are not necessarily useful everywhere you might use HashMap or ArrayList, but are designed to optimize specific common situations. 
- **ConcurrentHashMap does not allow null** keys or null values while **synchronized HashMap allows one null key**.

# Synchronized List
- CopyOnWriteArrayList and CopyOnWriteArraySet
CopyOnWriteArrayList is a concurrent alternative of synchronized List. CopyOnWriteArrayList provides better concurrency than synchronized List by allowing **multiple concurrent reader** and **replacing the whole list on write** operation. Yes, write operation is costly on CopyOnWriteArrayList but it **performs better when there are multiple reader** and requirement of **iteration is more than writing**. Since CopyOnWriteArrayList Iterator also don't throw ConcurrencModificationException **it eliminates need to lock the collection during iteration**. Remember both ConcurrentHashMap and CopyOnWriteArrayList doesn't provides same level of locking as Synchronized Collection and achieves thread-safety by there locking and mutability strategy. So they perform better if requirements suits there nature. Similarly, CopyOnWriteArraySet is a concurrent replacement to Synchronized Set. See What is CopyOnWriteArrayList in Java for more details

- BlockingQueue
BlockingQueue is also one of better known collection class in Java 5. BlockingQueue makes it easy **to implement producer-consumer design pattern** by providing inbuilt **blocking support for put() and take() method**. put() method will block if Queue is full while take() method will block if Queue is empty. Java 5 API provides two concrete implementation of BlockingQueue in form of **ArrayBlockingQueue and LinkedBlockingQueue**, both of them implement **FIFO ordering** of element. ArrayBlockingQueue **is backed by Array** and its **bounded** in nature while **LinkedBlockingQueue is optionally bounded**. Consider **using BlockingQueue to solve producer Consumer problem** in Java instead of writing your won wait-notify code. Java 5 also provides **PriorityBlockingQueue**, another implementation of BlockingQueue which is ordered on priority and useful if you want to process elements on order other than FIFO.

-  Deque interface 
is added in Java 6 and it extends Queue interface to support **insertion and removal from both end of Queue** referred as **head and tail**. Java6 also provides concurrent implementation of Deque like **ArrayDeque and LinkedBlockingDeque**. Deque Can be used efficiently **to increase parallelism in program by allowing set of worker thread **to help each other by taking some of work load from other thread by utilizing Deque double end consumption property. So if all Thread has there **own set of task Queue and they are consuming from head**; helper thread can also share some work load via **consumption from tail**.

-  ConcurrentSkipListMap and ConcurrentSkipListSet
Just like ConcurrentHashMap provides a concurrent alternative of synchronized HashMap. **ConcurrentSkipListMap and ConcurrentSkipListSet provide concurrent alternative** for synchronized version of **SortedMap and SortedSet**. For example instead of using TreeMap or TreeSet wrapped inside synchronized Collection, You can consider using ConcurrentSkipListMap or ConcurrentSkipListSet from java.util.concurrent package. They also implement NavigableMap and NavigableSet to add additional navigation method we have seen in our post How to use NavigableMap in Java.


# To sort hashmap by key and value
- Why can't we use TreeMap in place of HashMap is the question appears in most Java programmer's mind when they asked to sort HashMap in Java. Well, TreeMap is way slower than HashMap because it runs sorting operation with each insertion, update and removal and sometimes you don't really need an all time sorted Map, What you need is an ability to sort any Map implementation based upon its key and value.
## Sort by Key
- As I said Map or HashMap in Java can be sorted either on keys or values. Sorting Map on keys is rather easy than sorting on values because Map **allows duplicate values but doesn't allow duplicates keys**. You can sort Map, be it HashMap or Hashtable by copying keys into List than sorting List by using Collections.sort() method, here you can use either Comparator or Comparable based upon whether you want to sort on a custom order or natural order. 
-Once List of keys is sorted, we can create another Map, particularly LinkedHashMap to insert keys in sorted order. LinkedHashMap will maintain the order on which keys are inserted, the result is a sorted Map based on keys. This is shown in the following example by writing a generic parameterized method to sort Map based on keys. You can also sort Map in Java by using TreeMap and Google Collection API (Guava). The advantage of using Guava is that you get some flexibility on specifying ordering.
## Sorting Map in Java - By Value
- To implement Collection.sort(map, new Comparator<Map.Entry<K,V>>(){ o1.getValue().compareTo(o2.getValue())
- But need to take care of null and duplication


# Reference 
- http://javarevisited.blogspot.in/2011/02/how-hashmap-works-in-java.html
- http://javarevisited.blogspot.in/2011/04/difference-between-concurrenthashmap.html
- http://javarevisited.blogspot.com/2013/02/concurrent-collections-from-jdk-56-java-example-tutorial.html#ixzz4WBYzKelD
- http://javarevisited.blogspot.com/2012/12/how-to-sort-hashmap-java-by-key-and-value.html#ixzz4WBgfeGVM
