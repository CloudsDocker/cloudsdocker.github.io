---
title: Algorithm
tags:
- Dev
- algorithm
layout: posts
---
# This page is about key points about Algorithm


## Methodology
- The easiest way to improve search efficiency on a set of data is to put it in a data structure that allows more efficient searching.
What data structures can be searched more efficiency than O(n)? Binary tree can be searched in O(log(n)). Arrays and hash tables both have constant time element look up (has tables have worse-case lookup of O(n) but the average case is O(1)).
- Then need to determine which data structure to be used. If the underlying characters are just ASCII, then a array[128] would be enough. But characters are UNICODe, then it need 100,000 (100K) array, which is a concern of memory, so hash table would be a better option, which only keep exist characters.
In general, arrays are a better choice for long strings with a limited set of possible characters values, hash tables are more efficient for shorter strings or when there are many possible character values.  
- For some problems, obvious iterative alternatives like the one just shown don’t exist, but it’s always possible to implement a recursive algorithm without using recursive calls.
- For a simple recursive function like factorial, many computer architectures spend more time on call overhead than on the actual calculation. Iterative functions, which use looping constructs instead of recursive function calls, do not suffer from this overhead and are frequently more efficient.
- NOTE Iterative solutions are usually more efficient than recursive solutions.
- NOTE Every recursive case must eventually lead to a base case.
- NOTE Recursive algorithms have two cases: recursive cases and base cases

# Sort
## I collections.sort()

```java
Object[] a = list.toArray();
        Arrays.sort(a);
        ListIterator<T> i = list.listIterator();
        for (int j=0; j<a.length; j++) {
            i.next();
            i.set((T)a[j]);
        }

```

##  Arrays.sort
```java
public static void sort(Object[] a) {
        if (LegacyMergeSort.userRequested)
            legacyMergeSort(a);
        else
            ComparableTimSort.sort(a);
    }
private static void mergeSort(Object[] src,
                                  Object[] dest,
                                  int low,
                                  int high,
                                  int off) {
        int length = high - low;

        // Insertion sort on smallest arrays
        if (length < INSERTIONSORT_THRESHOLD) { // threshold is 7
            for (int i=low; i<high; i++)
                for (int j=i; j>low &&
                         ((Comparable) dest[j-1]).compareTo(dest[j])>0; j--)
                    swap(dest, j, j-1);
            return;
        }

// else use mergeSort

```



# Self review
## CeasarCipher:

Generally: it’s a rotation of English alphabic. E.g. if rotation is 2, the encode is start from A+2, i.e. A is at -2 of the encode array. 
And decode is start with 26-2, and “A” start at positon 2, then the increase by 1 character to constitute the array
That’s why need to “%26”, to make it loop across 26 characters

```sh
If rotation is 2:
--- encrytpion code is:[C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, A, B]
--- decrytpion code is:[Y, Z, A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X]
If rotation is 4:
--- encrytpion code is:[E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, A, B, C, D]
--- decrytpion code is:[W, X, Y, Z, A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V]
```

```java
ABC:
Msg ={‘A’,’B’,’C’};
Char[] encode=’A’+(k+rotation)%26);
Char[] decode=’A’+(k-rotation+26)%26); // +26 to avoid negative

Encode={‘C’,’D’,’E’}; // rotation=3, so A+3, A+4,A+5,xxx, A+26=>3,4,5,6,xxx,0
Decode={‘M’,’N’,’O’};//as k-rotation+26 % 26, so it’s 26-3+0,26-3+1 ,xx: => 23,24,25,0,1,2,3,4,is: A+23,A+24,A+25=>‘M’,’N’,’O’. that’s rotation, rotain-1, rotaion -2 xxxx
For(int i=0;i<msg.length;i++){
  Int j=msg[i]-‘A’; // to remove the base ‘A”, so sync with the “k” in encode, 3,4,5,xxx 3+26
  Msg[i]=codes[j];
}
// encode
Int j=’A’-‘A’; //0
Msg[0]=’C’;
Msg[1]=’D’;
Msg[2]=’E’;

//decode
Int j=msg[i]-‘A’; //’C’-‘A’=3
Msg[i]=decode[j]; // correspoindg to the postion 0,-xxx, 26 in decode, 
Msg[0]=
```

- If you says “tree,” it’s a good idea to clarify whether she is referring to a generic tree or a binary tree.

# To print content of Array
```java
Import java.util.Arrays;
Arrays.toString(ary);
Arrays.deepToString(ary);
```

# search without recursive
Node findNode( Node root, int value ){
    while( root != null ){
        int currval = root.getValue();
        if( currval == value ) break;
        if( currval < value ){
            root = root.getRight();
        } else { // currval > value
            root = root.getLeft();
        }
    }

    return root;
}

- preceding lookup operation can be reimplemented recursively as follows:
Node findNode( Node root, int value ){
    if( root == null ) return null;
    int currval = root.getValue();        
    if( currval == value ) return root;           
    if( currval < value ){
        return findNode( root.getRight(), value );
    } else { // currval > value
        return findNode( root.getLeft(), value );
    }  
}

- This subtree property is conducive to recursion because recursion generally involves solving a problem in terms of similar subproblems and a base case. 

# Big O sequencey
1, logn, n, n log n, n2, n3, 2n(2 power n).

# Big O
- It is also considered poor taste to include constant factors and lower-order terms in the big-Oh notation. For example, it is not fashionable to say that the function 2n2 is O(4n2 + 6n log n), although this is completely correct. We should strive instead to describe the function in the big-Oh **in simplest terms**.
- So, for example, we would say that an algorithm that runs in worst-case time 4n2 + n log n is a quadratic-time algorithm, since it runs in O(n2) time. Likewise, an algorithm running in time at most 5n + 20logn + 4 would be called a linear-time algorithm.

# Big Omega
- Just as the big-Oh notation provides an asymptotic way of saying that a function is “less than or equal to” another function, the following notations provide **an asymptotic way** of saying that a function grows at a rate that is “**greater than or equal to**” that of another.
- Example 4.14: 3n log n ? 2n is Ω(n log n).

# Big-Theta
- In addition, there is a notation that allows us to say that two functions grow at the same rate, up to constant factors. We say that f(n) is Θ(g(n)), pronounced “f(n) is big-Theta of g(n),”

# Comparative Analysis
- asymptotically[,?simp't?tik,-k?l] better
- Suppose two algorithms solving the same problem are available: an algorithm A, which has a running time of O(n), and an algorithm B, which has a running time of O(n2). Which algorithm is better? We know that n is O(n2), which implies that algorithm A **is asymptotically better** than algorithm B, although for a small value of n, B may have a lower running time than A.


# Some Words of Caution
- First, note that the use of the big-Oh and related notations can be somewhat misleading should the constant factors they “hide” be very large. For example, while it is true that the function 10100n is O(n), if this is the running time of an algorithm being compared to one whose running time is 10n log n, we should prefer the O(nlog n)-time algorithm, even though the linear-time algorithm is asymptotically faster. This preference is because the constant factor, 10100, which is called “one googol,” is believed by many astronomers to be an upper bound on the number of atoms in the observable universe. So we are unlikely to ever have a real-world problem that has this number as its input size.

# Exponential [,eksp?'nen?(?)l] Running Times
- To see how fast the function 2n grows, consider the famous story about the inventor of the game of chess. He asked only that his king pay him 1 grain of rice for the first square on the board, 2 grains for the second, 4 grains for the third, 8 for the fourth, and so on. The number of grains in the 64th square would be
263 = 9, 223, 372, 036, 854, 775, 808,
which is about nine billion billions!
- If we must draw a line between efficient and inefficient algorithms, therefore, it is natural to make this distinction be that between those algorithms running in **polynomial [,p?l?'n??m??l] time** and those running in **exponential time**. That is, make the distinction between algorithms with a running time that is **O(nc)** (power c based on n), for some constant c > 1, and those with a running time that is **O(bn)** (power n based on b), for some constant b > 1. Like so many notions we have discussed in this section, this too should be taken with a “grain of salt,” for an algorithm running in O(n100) time should probably not be considered “efficient.” Even so, the distinction between polynomial-time and exponential-time algorithms is considered a robust measure of tractability.

# Examples of Algorithm Analysis
## constant time operation
- All of the primitive operations, originally described on page 154, are assumed to run in constant time; Assume that variable A is an array of n elements. The expression A.length in Java is evaluated in constant time, because arrays are represented internally with an explicit variable that records the length of the array. Another central behavior of arrays is that for any valid index j, the individual element, A[j], can be accessed in constant time. This is because an array uses a consecutive block of memory. The jth element can be found, not by iterating through the array one element at a time, but by validating the index, and using it as an offset from the beginning of the array in determining the appropriate memory address. Therefore, we say that the expression A[j] is evaluated in O(1) time for an array.

## Finding the Maximum of an Array
Proposition 4.16: The algorithm, arrayMax, for computing the maximum element of an array of n numbers, runs in O(n) time.

Justification: The initialization at lines 3 and 4 and the return statement at line 8 require only a constant number of primitive operations. Each iteration of the loop also requires only a constant number of primitive operations, and the loop executes n ? 1 times.

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

# by sorting
Sorting algorithms will be the focus of Chapter 12. The best sorting algorithms (including those used by Array.sort in Java) guarantee a worst-case running time of O(nlog n). Once the data is sorted, the subsequent loop runs in O(n) time, and so the entire unique2 algorithm runs in O(n log n) time. Exercise C-4.35 explores the use of sorting to solve the three-way set disjointness problem in O(n log n) time.

# prefixAverage
Check the source code at PrefixAverage.java, the inital implementation is two for loop, which is O(n<sup>2</sup>), while the better approach is reuse existing total sum.
```java
// naiive approach,
for (int i = 0; i < n; i++) {
			double total=0;
			for (int j = 0; j <=i; j++) { // be awre it's <=, instead of "<"
				total+=x[j];				
			}
			a[i]=total/(i+1);			
		}
// better approach
double total=0;
		for (int i = 0; i < n; i++) {
			total += x[i];
			a[i]=total/(i+1);			
		}
```

# Recursive
## Definitions
1. We have one or more **base cases**, which refer to fixed values of the function. e.g. for n!=1 as  n=1 is base.
1. Then we have one or more **recursive cases**, which define the function in terms of itself. for n!, it's =n*(n-1)! for n>=1
- Repetition is achieved through repeated recursive invocations of the method. The process i finite because each time the method is invoked, its argument is smaller by one, and when a base case is reached, no further recursive calls are made.
- In the case of computing the factorial function, there is no compelling reason for prefereing recursion over a direct iteration with a loop.

# Tree
## ADT (Abstract Data Type)
- we define a tree ADT using the concept of a position as an abstraction for a node of a tree. An element is stored at each position, and positions satisfy parent-child relationships that define the tree structure. 

## Depth and Height 
### Depth
- The depth of p is the number of ancestors of p, other than p itself.
- The running time of depth(p) for position p is O(dp + 1), where dp denotes the depth of p in the tree, because the algorithm performs a constant-time recursive step for each ancestor of p. Thus, algorithm depth(p) runs in O(n) worst-case time, where n is the total number of positions of T, because a position of T may have depth n - 1 **if all nodes form a single branch**. 
- Method depth, as implemented within the AbstractTree class.
```java
public int depth(Position<E> p){
	if(isRoot(p))
		return 0;
	else
		return 1+depth(parent(p));
}
```
### Height
- We next define the height of a tree to be equal to the maximum of the depths of its positions (or zero, if the tree is empty).
- Folloing worst time cost is O(n), it progresses in a **top-down** fashion.
- If the method is initially called on the root of T, it will eventually be called once for each position of T. This is because the root eventually invokes the recursion on each of its children, which in turn invokes the recursion on each of their children, and so on.
```java
public int height(Position<E> p){
	int h=0;
	for(Position<E> c: children(p))
		h=Math.max(h,1+height(c));
	return h;
}
```

## Binary Tree
- A binary tree is an ordered tree with the following properties:
   - Every node has at most two children.
   - Each child node is labeled as being either a left child or a right child.
   - A left child precedes a right child in the order of children of a node.
- A binary **tree is proper if each node has either zero or two children**. Some people also refer to **such trees as being full binary trees**. Thus, **in a proper binary tree, every internal node has exactly two children**. A binary tree that is not proper is **improper**.
### Some binary trees
#### decision tree
- An important class of binary trees arises in contexts where we wish to represent a number of different outcomes that can result from answering a series of yes-or-no questions. Each internal node is associated with a question. Starting at the root, we go to the left or right child of the current node, depending on whether the answer to the question is “Yes” or “No.” With each decision, we follow an edge from a parent to a child, eventually tracing a path in the tree from the root to a leaf. Such binary trees are known as decision trees, because a leaf position p in such a tree represents a decision of what to do if the questions associated with p's ancestors are answered in a way that leads to p. **A decision tree is a proper binary tree**. 
#### Arithmetic expression
- An arithmetic expression can be represented by a binary tree whose leaves are associated with variables or constants, and whose internal nodes are associated with one of the operators +, ?, *, and /, as demonstrated in Figure 8.6. Each node in such a tree has a value associated with it.
   - If a node is leaf, then its value is that of its variable or constant.
   - If a node is internal, then its value is defined by applying its operation to the values of its children.
### Properties of Binary trees
- level d has at most 2<sup>d</sup> nodes
- Let T be a nonempty binary tree, and let n, nE, nI, and h denote the number of nodes, number of external nodes, number of internal nodes, and height of T, respectively. Then T has the following properties:
   - h + 1 ≤ n ≤ 2<sup>h+1</sup> - 1
   - 1 ≤ nE ≤ 2<sup>h</sup>
   - h ≤ nI ≤ 2<sup>h</sup> - 1
   - log(n + 1) - 1 ≤ h ≤ n - 1

- Also, if T is proper, then T has the following properties:
   - 2h + 1 ≤ n ≤ 2<sup>h+1</sup> - 1
   - h + 1 ≤ nE ≤ 2<sup>h</sup>
   - h ≤ nI ≤ 2<sup>h</sup> - 1
   - log(n + 1) - 1 ≤ h ≤ (n - 1)/2
-  In a nonempty proper binary tree T, with nE external nodes and nI internal nodes, we have nE = nI + 1.


# Why use tree
- You can search, insert/delete items quickly in a tree
- Ordered Arrays are bad at Insertions/Deletions
- Finding items in a Linkedlist is slow
- Time needed to perform an operation on a tree is O(log N)
- On average a tree is more efficient if you need to perform many different types of operations.

# Code practice
http://www.practice.geeksforgeeks.org/problem-page.php?pid=700159

# Geek IDE
http://code.geeksforgeeks.org/index.php

# Reference
- http://www.geeksforgeeks.org/maximum-width-of-a-binary-tree/
