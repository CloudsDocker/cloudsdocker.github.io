---
title: Tips about algorithm resolving from Leetcode
date: 2020-07-04
layout: posts
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


# BFS & DFS

BFS 的核心思想应该不难理解的，就是把一些问题抽象成图，从一个点开 始，向四周开始扩散。`一般来说，我们写 BFS 算法都是用「队列」这种数 据结构`，每次将一个节点周围的所有节点加入队列。
BFS 相对 DFS 的最主要的区别是: `BFS 找到的路径一定是最短的，但代价 就是空间复杂度比 DFS 大很多`，


## Use case for BFS

我们先举例一下 BFS 出现的常⻅场景好吧，问题的本质就 是让你在一幅「图」中找到从起点 start 到终点 target 的最近距离，这 个例子听起来很枯燥，但是 BFS 算法问题其实都是在干这个事儿

这个广义的描述可以有各种变体，比如走迷宫，有的格子是围墙不能走，从起点到终点的最短距离是多少?如果这个迷宫带「传送门」可以瞬间传送呢?

再比如说两个单词，要求你通过某些替换，把其中一个变成另一个，每次只能替换一个字符，最少要替换几次?

### BFS template
```java
// 计算从起点 start 到终点 target 的最近距离 
int BFS(Node start, Node target) {
	Queue<Node> q; // 核心数据结构 Set<Node> visited; // 避免走回头路
	q.offer(start); // 将起点加入队列 visited.add(start);
	int step = 0; // 记录扩散的步数
	while (q not empty) {
		int sz = q.size();
		/* 将当前队列中的所有节点向四周扩散 */ 
		for (int i = 0; i < sz; i++) {
			Node cur = q.poll();
			/* 划重点:这里判断是否到达终点 */
			if (cur is target)
			    return step;
			/* 将 cur 的相邻节点加入队列 */ 
			for (Node x : cur.adj())
				if (x not in visited) { 
					q.offer(x);
					visited.add(x); 
				}
			/* 划重点:更新步数在这里 */
			step++; 
		}
}
```

怎么套到 BFS 的框架里呢?首先明确一下起点 start 和终点 target 是什 么，怎么判断到达了终点?
显然起点就是 root 根节点，终点就是最靠近根节点的那个「叶子节点」 嘛，叶子节点就是两个子节点都是 null 的节点:

```java
  int minDepth(TreeNode root) {
  	if (root == null) return 0; 
  	Queue<TreeNode> q = new LinkedList<>(); 
  	q.offer(root);
// root 本身就是一层，depth 初始化为 1
int depth = 1;
while (!q.isEmpty()) {
int sz = q.size();
/* 将当前队列中的所有节点向四周扩散 */ 
for (int i = 0; i < sz; i++) {
TreeNode cur = q.poll();
/* 判断是否到达终点 */
if (cur.left == null && cur.right == null)
return depth;
/* 将 cur 的相邻节点加入队列 */ if (cur.left != null)
q.offer(cur.left); if (cur.right != null)
q.offer(cur.right);
}
/* 这里增加步数 */
depth++; }
    return depth;
}
```

什么 BFS 可以找到最短距离，DFS 不行吗?
首先，你看 BFS 的逻辑， depth 每增加一次，队列中的所有节点都向前迈一步，这保证了第一次到达终点的时候，走的步数是最少的。

形象点说，DFS 是线，BFS 是面;DFS 是单打独斗，BFS 是集体行动。这个应该比较容易理解吧。

既然 BFS 那么好，为啥 DFS 还要存在?
BFS 可以找到最短距离，但是空间复杂度高，而 DFS 的空间复杂度较低。
还是拿刚才我们处理二叉树问题的例子，假设给你的这个二叉树是满二叉 树，节点数为 N ，对于DFS算法来说，空间复杂度无非就是递归堆栈，最 坏情况下顶多就是树的高度，也就是 O(logN) 。
但是你想想 BFS 算法，队列中每次都会储存着二叉树一层的节点，这样的 话最坏情况下空间复杂度应该是树的最底层节点的数量，也就是 N/2 ，用 BigO表示的话也就是 O(N) 。
由此观之，BFS 还是有代价的，一般来说在找最短路径的时候使用 BFS， 其他时候还是 DFS 使用得多一些(主要是递归代码好写)。

# Dynamic Porgramming

动态规划的一般流程就是三步:暴力的递归解法 -> 带备忘录的 递归解法 -> 迭代的动态规划解法。
就思考流程来说，就分为一下几步:找到状态和选择 -> 明确 dp 数组/函数 的定义 -> 寻找状态之间的关系。

## Backpack
遇到背包问题可以说是手到擒来好吧。 无非就是状态 + 选择，也没啥特别之处嘛。


## Super Egg Drop
### 思路分析
对动态规划问题，直接套我们以前多次强调的框架即可:这个问题有什么「状态」，有什么「选择」，然后穷举。

「状态」很明显，就是当前拥有的鸡蛋数 K 和需要测试的楼层数 N 。随 着测试的进行，鸡蛋个数可能减少，楼层的搜索范围会减小，这就是状态的 变化。
「选择」其实就是去选择哪层楼扔鸡蛋。回顾刚才的线性扫描和二分思路， 二分查找每次选择到楼层区间的中间去扔鸡蛋，而线性扫描选择一层层向上 测试。不同的选择会造成状态的转移。
现在明确了「状态」和「选择」，动态规划的基本思路就形成了:肯定是个 二维的 dp 数组或者带有两个状态参数的 dp 函数来表示状态转移;外加 一个 for 循环来遍历所有选择，择最优的选择更新状态:



我们选择在第 i 层楼扔了鸡蛋之后，可能出现两种情况:鸡蛋碎了，鸡蛋 没碎。注意，这时候状态转移就来了:
如果鸡蛋碎了，那么鸡蛋的个数 K 应该减一，搜索的楼层区间应该从 [1..N] 变为 [1..i-1] 共 i-1 层楼;
如果鸡蛋没碎，那么鸡蛋的个数 K 不变，搜索的楼层区间应该从 [1..N] 变为 [i+1..N] 共 N-i 层楼。

# Reference
- https://labuladong.gitbook.io/algo/
