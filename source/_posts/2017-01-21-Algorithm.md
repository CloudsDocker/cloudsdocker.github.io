---
title: Algorithm
tag: algorithm
---


# Big O sequencey
1, logn, n, n log n, n2, n3, 2n(2 power n).

# Big O
- It is also considered poor taste to include constant factors and lower-order terms in the big-Oh notation. For example, it is not fashionable to say that the function 2n2 is O(4n2 + 6n log n), although this is completely correct. We should strive instead to describe the function in the big-Oh **in simplest terms**.
- So, for example, we would say that an algorithm that runs in worst-case time 4n2 + n log n is a quadratic-time algorithm, since it runs in O(n2) time. Likewise, an algorithm running in time at most 5n + 20logn + 4 would be called a linear-time algorithm.

# Big Omega
- Just as the big-Oh notation provides an asymptotic way of saying that a function is “less than or equal to” another function, the following notations provide **an asymptotic way** of saying that a function grows at a rate that is “**greater than or equal to**” that of another.
- Example 4.14: 3n log n − 2n is Ω(n log n).

# Big-Theta
- In addition, there is a notation that allows us to say that two functions grow at the same rate, up to constant factors. We say that f(n) is Θ(g(n)), pronounced “f(n) is big-Theta of g(n),” 

# Comparative Analysis
- asymptotically[,æsimp'tɔtik,-kəl] better
- Suppose two algorithms solving the same problem are available: an algorithm A, which has a running time of O(n), and an algorithm B, which has a running time of O(n2). Which algorithm is better? We know that n is O(n2), which implies that algorithm A **is asymptotically better** than algorithm B, although for a small value of n, B may have a lower running time than A.


# Some Words of Caution
- First, note that the use of the big-Oh and related notations can be somewhat misleading should the constant factors they “hide” be very large. For example, while it is true that the function 10100n is O(n), if this is the running time of an algorithm being compared to one whose running time is 10n log n, we should prefer the O(nlog n)-time algorithm, even though the linear-time algorithm is asymptotically faster. This preference is because the constant factor, 10100, which is called “one googol,” is believed by many astronomers to be an upper bound on the number of atoms in the observable universe. So we are unlikely to ever have a real-world problem that has this number as its input size.

# Exponential [,ekspə'nenʃ(ə)l] Running Times
- To see how fast the function 2n grows, consider the famous story about the inventor of the game of chess. He asked only that his king pay him 1 grain of rice for the first square on the board, 2 grains for the second, 4 grains for the third, 8 for the fourth, and so on. The number of grains in the 64th square would be
263 = 9, 223, 372, 036, 854, 775, 808,
which is about nine billion billions!
- If we must draw a line between efficient and inefficient algorithms, therefore, it is natural to make this distinction be that between those algorithms running in **polynomial [,pɒlɪ'nəʊmɪəl] time** and those running in **exponential time**. That is, make the distinction between algorithms with a running time that is **O(nc)** (power c based on n), for some constant c > 1, and those with a running time that is **O(bn)** (power n based on b), for some constant b > 1. Like so many notions we have discussed in this section, this too should be taken with a “grain of salt,” for an algorithm running in O(n100) time should probably not be considered “efficient.” Even so, the distinction between polynomial-time and exponential-time algorithms is considered a robust measure of tractability.

# Examples of Algorithm Analysis
## constant time operation
- All of the primitive operations, originally described on page 154, are assumed to run in constant time; Assume that variable A is an array of n elements. The expression A.length in Java is evaluated in constant time, because arrays are represented internally with an explicit variable that records the length of the array. Another central behavior of arrays is that for any valid index j, the individual element, A[j], can be accessed in constant time. This is because an array uses a consecutive block of memory. The jth element can be found, not by iterating through the array one element at a time, but by validating the index, and using it as an offset from the beginning of the array in determining the appropriate memory address. Therefore, we say that the expression A[j] is evaluated in O(1) time for an array.

## Finding the Maximum of an Array
Proposition 4.16: The algorithm, arrayMax, for computing the maximum element of an array of n numbers, runs in O(n) time.

Justification: The initialization at lines 3 and 4 and the return statement at line 8 require only a constant number of primitive operations. Each iteration of the loop also requires only a constant number of primitive operations, and the loop executes n − 1 times. 

## Composing Long Strings
- Therefore, the overall time taken by this algorithm is proportional to
1 + 2 + ··· + n,
which we recognize as the familiar O(n<sup>2</sup>) summation from Proposition 4.3. Therefore, the total time complexity of the repeat1 algorithm is O(n<sup>2</sup>).

- x = logbn if and only if bx = n.
The value b is known as the base of the logarithm. Note that by the above definition, for any base b > 0, we have that logb 1 = 0.


# Three-Way Set Disjointness
## Origional solution
Suppose we are given three sets, A, B, and C, stored in three different integer arrays. We will assume that no individual set contains duplicate values, but that there may be some numbers that are in two or three of the sets. The three-way set disjointness problem is to determine if the intersection of the three sets is empty, namely, that there is no element x such that x ∈ A, x ∈ B, and x ∈ C. 

```java
    private static boolean disjoint1(int[]  groupA, int[] groupB, int[] groupC){
        for ( int i : groupA) {
            for (int j : groupB) {
                for (int k : groupC) {
                    if(i==j && j==k){
                        return false;
                    }
                }
            }
        }
        return true;
    }
```
- This simple algorithm loops through each possible triple of values from the three sets to see if those values are equivalent. If each of the original sets has size n, then the worst-case running time of this method is O(n<sup>3</sup>) .
```java
private static boolean disjoint2(int[]  groupA, int[] groupB, int[] groupC){
        for ( int i : groupA) {
            for (int j : groupB) {
                if(i==j){
                    // add this checking to reduce complexitiy
                    for (int k : groupC) {
                        if(j==k){
                            return false;
                        }
                    }
                }
                
            }
        }
        return true;
    }
```

In the improved version, it is not simply that we save time if we get lucky. We claim that the worst-case running time for disjoint2 is O(n<sup>2</sup>). 

# Code practice
http://www.practice.geeksforgeeks.org/problem-page.php?pid=700159

# Geek IDE
http://code.geeksforgeeks.org/index.php

# Reference
- http://www.geeksforgeeks.org/maximum-width-of-a-binary-tree/