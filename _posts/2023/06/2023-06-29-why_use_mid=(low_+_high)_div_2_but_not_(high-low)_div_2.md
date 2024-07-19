---
title: why use mid = (low + high) // 2 but not (high-low)//2
header:
    image: /assets/images/why_use_mid=(low_+_high)_div_2_but_not_(high-low)_div_2.jpg
date: 2023-06-29
tags:
- AI
- Algo
- Programming

permalink: /blogs/tech/en/why_use_mid=(low_+_high)_div_2_but_not_(high-low)_div_2
layout: single
category: tech
---
> "Don't let yesterday take up too much of today." - Will Rogers

# One important trick in binary search: Why  mid = (low + high) // 2 but not (high-low)//2

Your must heard about binary research in Algorihthm (below is one sample).
```python
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1  # Target not found

```

But here is a question: why use mid = (low + high) // 2 but not (high-low)//2? 


The expression mid = (low + high) // 2 is used in the binary search algorithm to calculate the middle index of the current search range. It computes the average of the low and high indices and rounds down to the nearest integer using the floor division operator //.

Using (high - low) // 2 instead of (low + high) // 2 would not give the correct middle index. Let's consider an example to understand why:

Suppose low = 2 and high = 8, representing the current search range of indices. If we calculate (high - low) // 2, we get (8 - 2) // 2 = 6 // 2 = 3. However, the correct middle index should be (low + high) // 2 = (2 + 8) // 2 = 10 // 2 = 5.

The reason we add low and high before dividing by 2 is that low represents the starting index of the current search range, and high represents the ending index. By averaging them, we obtain the middle index, which helps in dividing the search range into two halves.

Using (high - low) // 2 would give the distance between low and high divided by 2, but it wouldn't take into account the starting index low. It would provide an incorrect index within the current search range.

Therefore, (low + high) // 2 is the correct way to calculate the middle index in the binary search algorithm, ensuring that the search range is correctly divided.
--HTH--
