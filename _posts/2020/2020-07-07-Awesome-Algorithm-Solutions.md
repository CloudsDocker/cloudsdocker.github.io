---
title: Awesome solutions for algorithm questions
date: 2020-06-29
layout: posts
---
你就会发现只要涉及递归的问题，都是 树的问题。

# Different Trees
- Full Binary Tree : For every node, it can either has no children or two children
- Complete Binary Tree: Leaf nodes are aligned leftwards (it must be left child if there is only one child)
- Perfect Binary Tree: every node has two children


但是必须说明的是，不管怎么优化，都符合回溯框架，而且时间复杂度都不 可能低于 O(N!)，因为穷举整棵决策树是无法避免的。这也是回溯算法的一 个特点，不像动态规划存在重叠子问题可以优化，回溯算法就是纯暴力穷 举，复杂度一般都很高。



```java
vector<vector<string>> res;
/* 输入棋盘边⻓ n，返回所有合法的放置 */ vector<vector<string>> solveNQueens(int n) {
// '.' 表示空，'Q' 表示皇后，初始化空棋盘。 vector<string> board(n, string(n, '.')); backtrack(board, 0);
return res;
}
// 路径:board 中小于 row 的那些行都已经成功放置了皇后 // 选择列表:第 row 行的所有列都是放置皇后的选择
// 结束条件:row 超过 board 的最后一行
void backtrack(vector<string>& board, int row) {
// 触发结束条件
if (row == board.size()) {
res.push_back(board);
return; }
int n = board[row].size();
for (int col = 0; col < n; col++) {
// 排除不合法选择
if (!isValid(board, row, col))
continue; // 做选择
board[row][col] = 'Q';
// 进入下一行决策 backtrack(board, row + 1); // 撤销选择
board[row][col] = '.';

}
}
/* 是否可以在 board[row][col] 放置皇后? */
bool isValid(vector<string>& board, int row, int col) {
int n = board.size();
// 检查列是否有皇后互相冲突
for (int i = 0; i < n; i++) {
    if (board[i][col] == 'Q')
        return false;
}
// 检查右上方是否有皇后互相冲突 for (int i = row - 1, j = col i >= 0 && j < n; i--,
+ 1; j++) {
    if (board[i][j] == 'Q')
        return false;
}
// 检查左上方是否有皇后互相冲突 for (int i = row - 1, j = col
- 1;
i >= 0 && j >= 0; i--, j--) {
        if (board[i][j] == 'Q')
            return false;
}
    return true;
}
```

### Suduko

有的时候，我们并不想得到所有合法的答案，只想要一个答案，怎么办呢? 比如解数独的算法，找所有解法复杂度太高，只要找到一种解法就可以。
其实特别简单，只要稍微修改一下回溯算法的代码即可:

### Backtrack summary
写 backtrack 函数时，需要维护走过的「路径」和当前可以做的「选择列 表」，当触发「结束条件」时，将「路径」记入结果集。
其实想想看，回溯算法和动态规划是不是有点像呢?我们在动态规划系列文 章中多次强调，动态规划的三个需要明确的点就是「状态」「选择」和 「base case」，是不是就对应着走过的「路径」，当前的「选择列表」和 「结束条件」?

# Binary Search
分析二分查找的一个技巧是:不要出现 else，而是把所有情况用 else if 写清 楚，这样可以清楚地展现所有细节。本文都会使用 else if，旨在讲清楚，读 者理解后可自行简化。


## 寻找左侧边界的二分搜索
以下是最常⻅的代码形式，其中的标记是需要注意的细节:
```java
int left_bound(int[] nums, int target)
{
  if (nums.length == 0) return -1;
  int left = 0;
  int right = nums.length; // 注意
  while (left < right) { // 注意
    int mid = (left + right) / 2;
    if (nums[mid] == target) {
            right = mid;
    } else if (nums[mid] < target) {
            left = mid + 1;
    } else if (nums[mid] > target) {
      right = mid; // 注意 }
    }
  }
    return left;
}
```


### Left left_bound
```java
int left_bound(int[] nums, int target) { int left = 0, right = nums.length - 1; // 搜索区间为 [left, right]
while (left <= right) {
int mid = left + (right - left) / 2; if (nums[mid] < target) {
// 搜索区间变为 [mid+1, right]
            left = mid + 1;
        } else if (nums[mid] > target) {
// 搜索区间变为 [left, mid-1]
right = mid - 1;
} else if (nums[mid] == target) {
// 收缩右侧边界
right = mid - 1; }
}
// 检查出界情况
if (left >= nums.length || nums[left] != target) return -1;
    return left;
}

```
这样就和第一种二分搜索算法统一了，都是两端都闭的「搜索区间」，而且 最后返回的也是 left 变量的值。只要把住二分搜索的逻辑，两种形式大 家看自己喜欢哪种记哪种吧。


### Right bound

寻找右侧边界的二分查找
类似寻找左侧边界的算法，这里也会提供两种写法，还是先写常⻅的左闭右
开的写法，只有两处和搜索左侧边界不同，已标注:
```java
int right_bound(int[] nums, int target) { if (nums.length == 0) return -1;
int left = 0, right = nums.length;
    while (left < right) {
        int mid = (left + right) / 2;
        if (nums[mid] == target) {
left = mid + 1; // 注意
} else if (nums[mid] < target) {
            left = mid + 1;
        } else if (nums[mid] > target) {
right = mid; }
}
return left - 1; // 注意 }
```

为什么这个算法能够找到右侧边界? 答:类似地，关键点还是这里:

```java
if (nums[mid] == target) {
    left = mid + 1;
    当 nums[mid] == target 时，不要立即返回，而是增大「搜索区间」的下界 left ，使得区间不断向右收缩，达到锁定右侧边界的目的。
```



是否也可以把这个算法的「搜索区间」也统一成两端都闭的形式呢?这 样这三个写法就完全统一了，以后就可以闭着眼睛写出来了。
答:当然可以，类似搜索左侧边界的统一写法，其实只要改两个地方就行 了:

```java
int right_bound(int[] nums, int target) { int left = 0, right = nums.length - 1; while (left <= right) {
    int mid = left + (right - left) / 2; if (nums[mid] < target) {
                left = mid + 1;
            } else if (nums[mid] > target) {
    right = mid - 1;
    } else if (nums[mid] == target) {
    // 这里改成收缩左侧边界即可
                left = mid + 1;
            }
    }
    // 这里改为检查 right 越界的情况，⻅下图
    if (right < 0 || nums[right] != target)
    return -1; return right;
    }
```


## Code tips

map.put(key, map.getOrDefault(key, 0) + 1)


## Sliding window concepts

滑动窗口算法的思路是这样:
1、我们在字符串 S 中使用双指针中的左右指针技巧，初始化 left = right = 0 ，把索引左闭右开区间 [left, right) 称为一个「窗口」。
2、我们先不断地增加 right 指针扩大窗口 [left, right) ，直到窗口中 的字符串符合要求(包含了 T 中的所有字符)。
3、此时，我们停止增加 right ，转而不断增加 left 指针缩小窗口 [left, right) ，直到窗口中的字符串不再符合要求(不包含 T 中的所有
字符了)。同时，每次增加 left ，我们都要更新一轮结果。
4、重复第 2 和第 3 步，直到 right 到达字符串 S 的尽头。

这个思路其实也不难，第 2 步相当于在寻找一个「可行解」，然后第 3 步在 优化这个「可行解」，最终找到最优解，也就是最短的覆盖子串。左右指针 轮流前进，窗口大小增增减减，窗口不断向右滑动，这就是「滑动窗口」这 个名字的来历。


## KPM
Be advised `shadow pointer` will only work for one case, that is the pattern with repeated char sets same as position zero

```java
// base case,  state will changed "0" -> "1" for given char at 0
  dp[0][pattern.charAt(0)]=1;
  int shaldow=0;
  for (int i = 1; i < n; i++) {
      // to traver each char
      for (int c = 0; c < 256; c++) {
          if(pattern.charAt(i)==c){
              dp[i][c]=i+1;    //[!!!!111] Not = dp[i][c]+1;, should be i+1
          }else{
              dp[i][c]=dp[shaldow][c];
          }
      }
      shaldow=dp[shaldow][pattern.charAt(i)];  // ONLY start from "0" to check with prefix and save time
  }
```


## max profit buy sell stock


### V2

Buy and sell stocks without any limitations
```java
public int maxProfit(int[] prices) {
    if(prices==null || prices.length<0)
        return 0;
    int n=prices.length;
    int profitNoholding=0,profitHolding=Integer.MIN_VALUE; // initially no transactions, the holding position will only be invalid
    for(int i=0;i<n;i++){
        int temp = profitNoholding;
        profitNoholding=Math.max(profitNoholding, profitHolding+prices[i]);
        profitHolding = Math.max(profitHolding, temp-prices[i]);
    }

    return profitNoholding;
}


public int maxProfit_best(int[] prices) {
    int total=0;
    // the philosophy is : add to total if current price is greater than previous one
    for(int i=1;i<prices.length;i++){
        if(prices[i]>prices[i-1]){
            total+=prices[i]-prices[i-1];
        }
    }
    return total;
}
}
```


# Next Greater Element

```java
class Solution {
    public int[] nextGreaterElements(int[] nums) {
        if(nums==null) return nums;
        // for next greater , monotonic stack
        Stack<Integer> stack = new Stack();
        int n=nums.length;
        int[] rtn=new int[n];
        // looped, so use "%n" + 2n for loop processing
        for(int i=2*n-1;i>=0;i--){
            // to strip off unqualified element, aka. to keep monotonic stak
            while(!stack.isEmpty() && stack.peek()<=nums[i%n]){ //[!!!!] be careful of bug, it should be "<=", rather than "<", becaust the question is "greater than", and it will add current element to stack, so if "=", it should be populate out as well
                stack.pop();
            }
            rtn[i%n]=stack.isEmpty()?-1:stack.peek();
            stack.push(nums[i%n]);
        }
    return rtn;
    }
}

```

# 递归反转整个链表

```java
ListNode reverse(ListNode head) {
if (head.next == null) 
    return head; 
ListNode last = reverse(head.next); 
head.next.next = head;
head.next = null;
return last;
}
```

对于递归算法，最重要的就是明确递归函数的定义。具体来说，我们的 reverse 函数定义是这样的:
输入一个节点 head ，将「以 head 为起点」的链表反转，并返回反转之 后的头结点。



