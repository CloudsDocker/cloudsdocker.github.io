---
header:
    image: /assets/images/hd_java_mistakes.png
title:  Some mistakes you'd avoid in java
date: 2022-02-23
tags:
 - lesson&learn
 - Java
 
permalink: /blogs/tech/en/tricky_mistakes_java
layout: single
category: tech
---

> With great power comes great responsibilities.


# Lambda

## Map vs ForEach
Please noted `map` won't **execute** code inside. If you want to make it invoked for each item, please replace it with `forEach`.

Lets assume one quesiont, which finding intersections of a list of arrays.

```java
public int[] intersectionOfArray(List<int[]> input) {
        List<Integer> list = new ArrayList<>();
        Map<Integer, Integer> map = new HashMap<>();
        Consumer<? super int[]> processRow=row-> Arrays.stream(row).forEach(it->map.put(it,map.getOrDefault(it,0)+1));
        input.forEach(processRow);
        Predicate<? super Map.Entry<Integer, Integer>> filterSize=entry->entry.getValue()==input.size();
        final int[] array = map.entrySet().stream().filter(filterSize).map(Map.Entry::getKey).mapToInt(i -> i).toArray();
        return array;
    }
```

Please be advised following line won't work if you replace `forEach` with `map`.

```java
Consumer<? super int[]> processRow=row-> Arrays.stream(row).forEach(it->map.put(it,map.getOrDefault(it,0)+1));
```

Above Function to be used in following

--End--



