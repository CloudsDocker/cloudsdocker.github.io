---
layout: page
title: HashMap in JDK
---
# Hashmap in JDK
Some note worth points about hashmap
- Lookup process
-- Step# 1: Quickly determine the bucket number in which this element may reside (using key.hashCode()).
-- Step# 2: Go over the mini-list and return the element that matches the key (using key.equals()).
- Immutability of keys
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

## Internal data structure
- transient Entry<K, V>[] elementData;
- transient int modCount = 0;
- private transient V[] cache;

## Put
It will call return putImpl(key, value); directly

### V putImpl(K key, V value) 
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
