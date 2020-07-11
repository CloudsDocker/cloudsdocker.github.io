---
title: Tips about algorithm resolving from Leetcode
date: 2020-07-04
---
Here are some tips and notes about how to resolve algorithm issues listed in LeetCode
# Rotation problem

## Rotate array

Here is one sample from Leetcode
```
189. Rotate Array
Given an array, rotate the array to the right by k steps, where k is non-negative.

Follow up:

Try to come up as many solutions as you can, there are at least 3 different ways to solve this problem.
Could you do it in-place with O(1) extra space?
 

Example 1:

Input: nums = [1,2,3,4,5,6,7], k = 3
Output: [5,6,7,1,2,3,4]
Explanation:
rotate 1 steps to the right: [7,1,2,3,4,5,6]
rotate 2 steps to the right: [6,7,1,2,3,4,5]
rotate 3 steps to the right: [5,6,7,1,2,3,4]
```
e.g. if k is bigger then array's length
```

```
### Tip 1: To find out the smallest rotate count

```java
class Solution {
    public void rotate(int[] nums, int k) {
    	// sample input 
    	// [1,2]
    	// 3
        k=k%nums.length; //[!!!!!] for 'rotation problem', firstly make sure to get smallest iterate count
        if(nums==null || k>nums.length) return ; //[!!! k>nums.length]
        int[] ori=Arrays.copyOf(nums,nums.length);
        for(int i=0;i<nums.length-k;i++){
            nums[i+k]=ori[i];
        }
        for(int i=0;i<k;i++){
            nums[i]=ori[nums.length-k+i];
        }
    }
}
```

Here is the runtime result

![](/images/Leetcode_189.png)

## Find next greater element in Rotate array 

首先，计算机的内存都是线性的，没有真正意义上的环形数组，但是我们可以模拟出环形数组的效果，一般是通过 \%% 运算符求模（余数），获得环形特效：

回到 Next Greater Number 的问题，增加了环形属性后，问题的难点在于：这个 Next 的意义不仅仅是当前元素的右边了，有可能出现在当前元素的左边（如上例）。

明确问题，问题就已经解决了一半了。我们可以考虑这样的思路：将原始数组 “翻倍”，就是在后面再接一个原始数组，这样的话，按照之前“比身高”的流程，每个元素不仅可以比较自己右边的元素，而且也可以和左边的元素比较了。



# Index Stack vs value Stack
Q: Can anyone please tell me the difference between stack and index stack? I mean which one to use on which problems?
A: When you need to use index, use the index. When you only need the value, both works.

So the rule of thumb is, if you only need value, both will work. However, if you need the index, for example, to compute the distance, e.g., how many days before getting a wammer day, or how many days the stock prices get higher, you will need to use the index. In such case, you can store index. Plus, you can store multiple pieces of information, such as a tuple (A[i], i, count)..., just an example.



# Binary Search
只要数组有序，就应该想到双指针技巧。


# Reference
- https://labuladong.gitbook.io/algo/