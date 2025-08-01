---
layout: posts
title: HashMap in JDK
tags:
- java
---
# Hashmap in JDK
## Some note worth points about hashmap
- Lookup process
   - Step# 1: Quickly determine the bucket number in which this element may reside (using key.hashCode()).
   - Step# 2: Go over the mini-list and return the element that matches the key (using key.equals()).
- Immutability of keys
- In Node<K,V> node of hashMap, besides key, value, hash, there is Node next link inside. So undelrying table is a linked list.
- For **get()**, firstly using hashcode calculation, divide by bucket number and get reminder, to locate the bucket, then compare key via ".euqals()", if matched, the value will be returned.
- Load factor and resize
When new hashHap is being populated, the linkedList associated with each bucket of source hashMap is iterated and nodes are copied to the destination bucket. However, note that these new nodes are prepended to the head of the destination linkedList. So resizing has an side effect of reversing the order of the items in the list. Default load factor for hashMap is 0.75.
- Worst-case performance:
In the worst case, a hashMap reduces to a linkedList.
However with Java 8, there is a change,
Java 8 intelligently determines if we are running in the worst-case performance scenario and converts the list into a binary search tree.
- Collisions
Collisions happen when 2 distinct keys generate the same hashCode() value. Multiple collisions are the result of bad hashCode() algorithm.There are many collision-resolution strategies - chaining, double-hashing, clustering.
However, java has chosen chaining strategy for hashMap, so in case of collisions, items are chained together just like in a linkedList.
- Some specialized hashMaps for specific purposes:
-- ConcurrentHashMap: HashMap to be used in multithreaded applications.
-- EnumMap: HashMap with Enum values as keys.
-- LinkedHashMap: HashMap with predictable iteration order (great for FIFO/LIFO caches)

## WeakReferenceMap, SoftReference Map etc.
Weak references (a WeakHashMap) aren't particularly good for this either, because as the elements in the cache become dereferenced by the application code they will quickly be removed from the cache by the garbage collector. This basically means there will be cache faults often (in other words, the cache lookups will fail).

Soft references can be very handy in situations such as this. Because soft references only exist if the memory is available, they can make very effective use of the space that is available. Unfortunately, although there is a WeakHashMap , there is no java.util.SoftHashMap . Why? I'm not really sure. Thankfully, a little trip back over to Jakarta-Commons-Collections digs up the org.apache.commons.collections.map.ReferenceMap .

SoftReferences are typically used for implementing memory caching. The JVM should try to keep softly referenced objects in memory as long as possible, and when memory is low clear the oldest soft references first. According to the JavaDoc, there are no guarantees though.

WeakReferences is the reference type I use most frequently. It's typically used when you want weak listeners or if you want to connect additional information to an object (using WeakHashMap for example). Very useful stuff when you want to reduce class coupling. 

Phantom references can be used to perform pre-garbage collection actions such as freeing resources. Instead, people usually use the finalize() method for this which is not a good idea. Finalizers have a horrible impact on the performance of the garbage collector and can break data integrity of your application if you're not very careful since the "finalizer" is invoked in a random thread, at a random time.

In the constructor of a phantom reference, you specify a ReferenceQueue where the phantom references are enqueued once the referenced objects becomes "phantom reachable". Phantom reachable means unreachable other than through the phantom reference. The initially confusing thing is that although the phantom reference continues to hold the referenced object in a private field (unlike soft or weak references), its getReference() method always returns null. This is so that you cannot make the object strongly reachable again.

From time to time, you can poll the ReferenceQueue and check if there are any new PhantomReferences whose referenced objects have become phantom reachable. In order to be able to to anything useful, one can for example derive a class from java.lang.ref.PhantomReference that references resources that should be freed before garbage collection. The referenced object is only garbage collected once the phantom reference becomes unreachable itself. 

## Source code analysis
### Internal data structure
- transient Entry<K, V>[] elementData;
- transient int modCount = 0;
- private transient V[] cache;

### Put
It will call return putImpl(key, value); directly

#### V putImpl(K key, V value) 
- if(key == null)
-- entry = findNullKeyEntry();
```java
entry = findNullKeyEntry();
            if (entry == null) {
                modCount++;
                entry = createHashedEntry(null, 0, 0);
                if (++elementCount > threshold) {
                    rehash();
                }
            }
```
--- findNullKeyEntry
Iterate the internal array to locate null entry
```java
final Entry<K,V> findNullKeyEntry() {
        Entry<K,V> m = elementData[0];
        while (m != null && m.key != null) {
            m = m.next;
        }
        return m;
    }
```
- else (if key is not null)
