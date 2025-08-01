---
title: Algorithm notes from Leecode -- 1
tags:
- Leetcode
- Algorithm
layout: posts
---
Algorithm Leetcode

Links

-   [[https://www.dailycodingproblem.com/?ref=csdojo]{.underline}](https://www.dailycodingproblem.com/?ref=csdojo)

-   [[https://www.csdojo.io/\#]{.underline}](https://www.csdojo.io/#)

-   https://github.com/mission-peace/interview/tree/master/src/com/interview/dynamic

-   [[https://leetcode.com/discuss/general-discussion/458695/dynamic-programming-patterns]{.underline}](https://leetcode.com/discuss/general-discussion/458695/dynamic-programming-patterns)

-   daily coding problem book pdf free download

[[https://github.com/CyC2018/CS-Notes/blob/master/notes/Leetcode%20题解%20-%20目录.md]{.underline}](https://github.com/CyC2018/CS-Notes/blob/master/notes/Leetcode%20%E9%A2%98%E8%A7%A3%20-%20%E7%9B%AE%E5%BD%95.md)

leetcodeGithub project in intelliJ

tasks to hands on

-   ~~0/1 knapsack~~

-   ~~fibnachi memoized and bottom up approaches~~

-   median of two sorted array

-   64 minimum path sum

-   

-   Maximum sub array (kadane algorithm)

-   

\[Slide Window\]

（1）没有重复字符的子字符的最大长度：给一个字符串，获得没有重复字符的最长子字符的长度

例子：

输入：\"abcbabcbb\"

输出：3

解释：因为没有重复字符的子字符是\'abc\'，所以长度是3

public class Solution {//时间复杂度O(2n)

//滑动窗口算法

public int **[lengthOfLongestSubstring]{.underline}**(String s) {

int n = s.length();

Set\<Character\> set = new HashSet\<\>();

int ans = 0, i = 0, j = 0;

while (i \< n && j \< n)
{//窗口的左边是i，右边是j，下列算法将窗口的左右移动，截取出其中一段

// try to extend the range \[i, j\]

if
(!set.contains(s.charAt(j))){//如果set中不存在该字母，就将j+1，相当于窗口右边向右移动一格，左边不动

set.add(s.charAt(j++));

ans = Math.max(ans, j - i);//记录目前存在过的最大的子字符长度

}

else
{//如果set中存在该字母，则将窗口左边向右移动一格，右边不动，直到该窗口中不存在重复的字符

set.remove(s.charAt(i++));

}

}

return ans;

}

}

作者：DrXu

链接：https://juejin.im/post/5c74a2e2f265da2dea053355

来源：掘金

著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。

====

### **解法3：优化的滑动窗口算法**

上面的滑动窗口算法最多需要2n的步骤，但这其实是能被优化为只需要n步。我们可以使用HashMap定义字符到索引之间的映射，然后，当我们发现子字符串中的重复字符时，可以直接跳过遍历过的字符了。

（2）public class Solution {//时间复杂度o(n)

public int lengthOfLongestSubstring(String s) {

int n = s.length(), ans = 0;

//使用hashmap记录遍历过的字符的索引，当发现重复的字符时，可以将窗口的左边直接跳到该重复字符的索引处

Map\<Character, Integer\> map = new HashMap\<\>(); // current index of
character

// try to extend the range \[i, j\]

for (int j = 0, i = 0; j \< n; j++)
{//j负责向右边遍历，i根据重复字符的情况进行调整

if (map.containsKey(s.charAt(j)))
{//当发现重复的字符时,将字符的索引与窗口的左边进行对比，将窗口的左边直接跳到该重复字符的索引处

i = Math.max(map.get(s.charAt(j)), i);

}

//记录子字符串的最大的长度

ans = Math.max(ans, j - i + 1);

//map记录第一次遍历到key时的索引位置，j+1,保证i跳到不包含重复字母的位置

map.put(s.charAt(j), j + 1);

}

return ans;

}

}

作者：DrXu

链接：https://juejin.im/post/5c74a2e2f265da2dea053355

来源：掘金

著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。

\[Slide Window\]

Min Windows

\-\-\-\-\-\-\-\-\-\-\-\-- best solution\-\--

（3）public static String **minWindowBetter**(String s, String t){

if(s==null\|\|t==null\|s.length()==0\|\|t.length()==0){

return \"\";

}

int left=0,right=0,count=0,min=Integer.MAX\_VALUE;

int pool\[\] = new int\[256\];

String rtn=\"\";

for(int i =0;i\<t.length();i++){

pool\[t.charAt(i)\]++;

}

while(right\<s.length()){

if(pool\[s.charAt(right++)\]\--\>0){//\[!\]

// (a) if(pool\[s.charAt(right++)\]\--\>=0), rather than
if(pool\[right++\]\--\>=0)

// (b) this is \"\>0\", but not \"\>=0\"

count++;

}

while(count==t.length()){

if((right-left)\<min){

min=right-left;

rtn=s.substring(left,right);

}

//shrink window

if(++pool\[s.charAt(left++)\]\>0){

count\--;

}

}

}

return rtn;

}

10 lines code to solve most "substring" problem

I will first give the solution then show you the magic template.

The code of solving this problem is below. It might be the shortest
among all solutions provided in Discuss.

string minWindow(string s, string t) {

vector\<int\> map(128,0);

for(auto c: t) map\[c\]++;

int counter=t.size(), begin=0, end=0, d=INT\_MAX, head=0;

while(end\<s.size()){

if(map\[s\[end++\]\]\--\>0) counter\--; //in t

while(counter==0){ //valid

if(end-begin\<d) d=end-(head=begin);

if(map\[s\[begin++\]\]++==0) counter++; //make it invalid

}

}

return d==INT\_MAX? \"\":s.substr(head, d);

}

Here comes the template.

For most substring problem, we are given a string and need to find a
substring of it which satisfy some restrictions. A general way is to use
a hashmap assisted with two pointers. The template is given below.

int findSubstring(string s){

vector\<int\> map(128,0);

int counter; // check whether the substring is valid

int begin=0, end=0; //two pointers, one point to tail and one head

int d; //the length of substring

for() { /\* initialize the hash map here \*/ }

while(end\<s.size()){

if(map\[s\[end++\]\]\-- ?){ /\* modify counter here \*/ }

while(/\* counter condition \*/){

/\* update d here if finding minimum\*/

//increase begin to make it invalid/valid again

if(map\[s\[begin++\]\]++ ?){ /\*modify counter here\*/ }

}

/\* update d here if finding maximum\*/

}

return d;

}

One thing needs to be mentioned is that when asked to find maximum
substring, we should update maximum after the inner while loop to
guarantee that the substring is valid. On the other hand, when asked to
find minimum substring, we should update minimum inside the inner while
loop.

The code of solving **[Longest Substring with At Most Two Distinct
Characters]{.underline}** is below:

（4）int lengthOfLongestSubstringTwoDistinct(string s) {

vector\<int\> map(128, 0);

int counter=0, begin=0, end=0, d=0;

while(end\<s.size()){

if(map\[s\[end++\]\]++==0) counter++;

while(counter\>2) if(map\[s\[begin++\]\]\--==1) counter\--;

d=max(d, end-begin);

}

return d;

}

The code of solving **[Longest Substring Without Repeating
Characters]{.underline}** is below:

Update 01.04.2016, thanks \@weiyi3 for advice.

**[（5）]{.underline}**int lengthOfLongestSubstring(string s) {

vector\<int\> map(128,0);

int counter=0, begin=0, end=0, d=0;

while(end\<s.size()){

if(map\[s\[end++\]\]++\>0) counter++;

while(counter\>0) if(map\[s\[begin++\]\]\--\>1) counter\--;

d=max(d, end-begin); //while valid, update d

}

return d;

}

I think this post deserves some upvotes! : )

**[\[sliding window \]]{.underline}**

string minWindow(string s, string t) {

unordered\_map\<char, int\> m;

// Statistic for count of char in t

for (auto c : t) m\[c\]++;

// counter represents the number of chars of t to be found in s.

size\_t start = 0, end = 0, counter = t.size(), minStart = 0, minLen =
INT\_MAX;

size\_t size = s.size();

// Move to find a valid window.

while (end \< size) {

// If char in s exists in t, decrease counter

if (m\[s\[end\]\] \> 0)

counter\--;

// Decrease m\[s\[end\]\]. If char does not exist in t, m\[s\[end\]\]
will be negative.

m\[s\[end\]\]\--;

end++;

// When we find a valid window, the move starts to find a smaller
window.

while (counter == 0) {

if (end - start \< minLen) {

minStart = start;

minLen = end - start;

}

m\[s\[start\]\]++;

// When char exists in t, increase the counter.

if (m\[s\[start\]\] \> 0)

counter++;

start++;

}

}

if (minLen != INT\_MAX)

return s.substr(minStart, minLen);

return \"\";

}

～～～～java version～～

public String minWindow(String s, String t) {

HashMap\<Character,Integer\> map = new HashMap();

for(char c : s.toCharArray())

map.put(c,0);

for(char c : t.toCharArray())

{

if(map.containsKey(c))

map.put(c,map.get(c)+1);

else

return \"\";

}

int start =0, end=0, minStart=0,minLen = Integer.MAX\_VALUE, counter =
t.length();

while(end \< s.length())

{

char c1 = s.charAt(end);

if(map.get(c1) \> 0)

counter\--;

map.put(c1,map.get(c1)-1);

end++;

while(counter == 0)

{

if(minLen \> end-start)

{

minLen = end-start;

minStart = start;

}

char c2 = s.charAt(start);

map.put(c2, map.get(c2)+1);

if(map.get(c2) \> 0)

counter++;

start++;

}

}

return minLen == Integer.MAX\_VALUE ? \"\" :
s.substring(minStart,minStart+minLen);

}

\[DP\]

**[（6]{.underline}**）longestCommonSubsequence

public int longestCommonSubsequence(String text1, String text2) {

// xx-est is meant for dynamic programming

// x keys for DP

// 1st, declare a DP table for bottom up

// 2nd set global value

// ================

// for top down, use memo

int m = text1.length(); //\[!!!!\] it\'s \"length()\" method for String

int n = text2.length();

int\[\]\[\] memo = new int\[m+1\]\[n+1\];

for(int i=0;i\<m;i++){

for(int j=0;j\<n;j++){

// if(i==0\|\|j==0){ //\[!!!!!222\] here is no need, because default
value in array is zero

// // 1st col or 1st row, set to 0

// memo\[i\]\[j\]=0;

// }else{

if(text1.charAt(i)==text2.charAt(j)){

memo\[i+1\]\[j+1\] = 1 + memo\[i\]\[j\];

}else{

// current char is different, so go to carry previous biggest value from
either left or up

memo\[i+1\]\[j+1\] = Math.max(memo\[i+1\]\[j\],memo\[i\]\[j+1\]);

}

// }

}

}

return memo\[m\]\[n\];

}

**\[DP\]**

LengthOfLIS

**[（7]{.underline}**）public class LengthOfLIS {

System.out.println(\"===test failed case (DP)
:\"+inst.lengthOfLIS\_tail(new int\[\]{4,10,4,3,8,9}));

System.out.println(\"===test failed case (DP)
:\"+inst.lengthOfLIS\_tail(new int\[\]{2,2})); //expect output \"1\"

public int lengthOfLIS\_naive(int\[\] nums){

//edge case

if(nums.length\<0){

return 0;

}

int m=nums.length;

int max=0; // global max

int\[\] dp=new int\[m\];

//embedded loop to search max value brute forcely

for (int i = 0; i \<m ; i++) {

// loop each digits

int localMax=0; // holder for MAX length of increase sequence before i

for (int j = 0; j \< i; j++) {

// loop to find all increasing BEFORE this number

if(dp\[j\]\>localMax && nums\[j\]\<nums\[i\]){

// previous number is SMALLER than i and greater than local max, that
means it\'s increasing

localMax=dp\[j\];

}

}

// after looped ALL previous numbers, add current one

dp\[i\]=localMax+1;

max = Math.max(max,dp\[i\]);

}

return max;

}

public int **[lengthOfLIS\_tail]{.underline}**(int\[\] nums){

int m=nums.length;

if(m==0) return 0;

int\[\] dp=new int\[m\]; // dp\[x\]=y : value \"y\" of dp stores \"the
last number\" (tail) of increasing sequence whose length is \"x\"

int maxLen=0;

dp\[0\]=nums\[0\];

//for loop each number in array

for (int i = 1; i \< m; i++) { //\[!!!!!!!!1111111\] it should start
with \"1\", as \"0\" is already setup

// there are 3 scenarios we need to update dp

if(nums\[i\]\<dp\[0\]){

// current number is even smaller than most smallest LIS, update it

dp\[0\]=nums\[i\];

}else if(nums\[i\]\>dp\[maxLen\]){

//current number is greater than \'tail\' of largest LIS, then update
the last LIS

dp\[++maxLen\]=nums\[i\];

}else{

// current number is in the middle, so we go to find the \*correct\*
position to locate the LIS in DP

dp\[binarySearchLIS(dp,0,maxLen,nums\[i\])\]=nums\[i\];

}

}

return maxLen+1; // because dp is zero based, so add one for result

}

public int **binarySearchLIS**(int\[\] dp, int min, int max, int
target){

while(min\<=max){

int middle =min + (max-min)/2; //\[!!!!!!!\] don\'t forget to add prefix
\"min +\" in front of (max-min)/2

if(dp\[middle\]==target){

return middle;

}else if(dp\[middle\]\>target){

max=middle-1;

} else if(dp\[middle\]\<target){

min=middle+1;

}

}

return min;

}

}

\[Graph\]

RottingOrange

**[（8]{.underline}**）public class GraphRottingOrange {

public static void main(String\[\] args) {

/\*

In a given grid, each cell can have one of three values:

the value 0 representing an empty cell;

the value 1 representing a fresh orange;

the value 2 representing a rotten orange.

Every minute, any fresh orange that is adjacent (4-directionally) to a
rotten orange becomes rotten.

Return the minimum number of minutes that must elapse until no cell has
a fresh orange. If this is impossible, return -1 instead.

Example 1:

Input: \[\[2,1,1\],\[1,1,0\],\[0,1,1\]\]

Output: 4

Example 2:

Input: \[\[2,1,1\],\[0,1,1\],\[1,0,1\]\]

Output: -1

Explanation: The orange in the bottom left corner (row 2, column 0) is
never rotten, because rotting only happens 4-directionally.

Example 3:

Input: \[\[0,2\]\]

Output: 0

Explanation: Since there are already no fresh oranges at minute 0, the
answer is just 0.

Note:

1 \<= grid.length \<= 10

1 \<= grid\[0\].length \<= 10

grid\[i\]\[j\] is only 0, 1, or 2.

\*/

GraphRottingOrange inst = new GraphRottingOrange();

# deleted 2-D array due to hexo error

System.out.println(\"===output of findRottenMinutes:\" +
inst.orangesRotting(grid));

}

public int orangesRotting(int\[\]\[\] grid) {

int m = grid.length;

int n = grid\[0\].length;

List\<String\> listRotten = new ArrayList\<\>();

List\<String\> listFresh = new ArrayList\<\>();

int nMinutes = 0;

//firstly, find and enlist rotten ones

for (int i = 0; i \< m; i++) {

for (int j = 0; j \< n; j++) {

if (grid\[i\]\[j\] == 2) {

//current cell is a rotten tomato, so check adjacent and contract them

listRotten.add(i + \"\" + j);

} else if (grid\[i\]\[j\] == 1) {

// fresh tomato, to record it , so check zero of this list to confirm
ALL tomato got infected

listFresh.add(i + \"\" + j);

}

}

}

// loop until empty of fresh ones

while (!listFresh.isEmpty()) {

List\<String\> infected = new ArrayList\<\>();

for (String strRotten : listRotten) {

int x = strRotten.charAt(0) - \'0\';

int y = strRotten.charAt(1) - \'0\';

//to search 4 directions both vertically and horizontally

# deleted 2-D array due to hexo error

for (int\[\] direction : directions) {

int newX = x + direction\[0\];

int newY = y + direction\[1\];

String newLoc = newX + \"\" + newY;

if (listFresh.contains(newLoc)) {

// make new tomato as rotten

listFresh.remove(newLoc);

// listRotten.add(newLoc);

infected.add(newLoc); // add to infected, rather than Rotten to avoid
\"ConcurrentModificationException\" as it\'s our loop list

}

}

}

// return -1 in case no more been infected

if (infected.isEmpty()) {

return -1;

}

// assign infected to listRotten to further check

listRotten=infected;

++nMinutes;

}

return nMinutes;

}

}

public int orangesRotting\_Iterative(int\[\]\[\] grid) {

if(grid == null \|\| grid.length == 0) return 0;

int rows = grid.length;

int cols = grid\[0\].length;

Queue\<int\[\]\> queue = new LinkedList\<\>();

int count\_fresh = 0;

//Put the position of all rotten oranges in queue

//count the number of fresh oranges

for(int i = 0 ; i \< rows ; i++) {

for(int j = 0 ; j \< cols ; j++) {

if(grid\[i\]\[j\] == 2) {

queue.offer(new int\[\]{i , j});

}

else if(grid\[i\]\[j\] == 1) {

count\_fresh++;

}

}

}

//if count of fresh oranges is zero \--\> return 0

if(count\_fresh == 0) return 0;

int count = 0;

# deleted 2-D array due to hexo error

//bfs starting from initially rotten oranges

while(!queue.isEmpty()) {

++count;

int size = queue.size();

for(int i = 0 ; i \< size ; i++) {

int\[\] point = queue.poll();

for(int dir\[\] : dirs) {

int x = point\[0\] + dir\[0\];

int y = point\[1\] + dir\[1\];

//if x or y is out of bound

//or the orange at (x , y) is already rotten

//or the cell at (x , y) is empty

//we do nothing

if(x \< 0 \|\| y \< 0 \|\| x \>= rows \|\| y \>= cols \|\|
grid\[x\]\[y\] == 0 \|\| grid\[x\]\[y\] == 2) continue;

//mark the orange at (x , y) as rotten

grid\[x\]\[y\] = 2;

//put the new rotten orange at (x , y) in queue

queue.offer(new int\[\]{x , y});

//decrease the count of fresh oranges by 1

count\_fresh\--;

}

}

}

return count\_fresh == 0 ? count-1 : -1;

}

\[DP\]

DecodeWays

package algo;

**[（9]{.underline}**）public class DecodeWays {

public static void main(String\[\] args) {

/\*

Similar questions:

62\. Unique Paths

70\. Climbing Stairs

509\. Fibonacci Number

91\. Decode Ways

A message containing letters from A-Z is being encoded to numbers using
the following mapping:

\'A\' -\> 1

\'B\' -\> 2

\...

\'Z\' -\> 26

Given a non-empty string containing only digits, determine the total
number of ways to decode it.

Example 1:

Input: \"12\"

Output: 2

Explanation: It could be decoded as \"AB\" (1 2) or \"L\" (12).

Example 2:

Input: \"226\"

Output: 3

Explanation: It could be decoded as \"BZ\" (2 26), \"VF\" (22 6), or
\"BBF\" (2 2 6).

\*/

DecodeWays inst = new DecodeWays();

System.out.println(\" decode ways: \"+ inst.numDecodings(\"12\"));

}

/\*

\"\"\"

s = 123

build up from right =\>

num\_ways (\"\") =\> 1 (empty string can be represented by empty string)
(i.e. num\_ways\[n\] = 1) NOTE: only for build up with a valid string.
Empty string on it\'s own doesn\'t need to be decoded.

num\_ways (\"3\") =\> 1 (only one way), i.e. num\_ways\[n-1\] = 1

num\_ways (\"23\") =\> \"23\" or \"2\"-\"3\",

num\_ways (\"33\") =\> \"3\"\"3\"

num\_ways (\"123\") =\> \"12\"(num\_ways(\"3\")) +
\"1\"(\"num\_ways(\"23\")) (i.e. num\_ways\[i+2\] + num\_ways\[i+1\])

num\_ways (\"323\") =\> \"3\"(num\_ways(\"23\")) (i.e. num\_ways\[i+1\])

so basically if s\[i:i+1\] (both included) \<= 26,

num\_ways\[i+2\] + num\_ways\[i+1\]

else:

num\_ways\[i+1\]

case with 0:

num\_ways (\"103\")

num\_ways (\"3\") =\> 1 (only one way)

num\_ways (\"03\") =\> 0 (can\'t decode 0)

num\_ways (\"003\") =\> \"00\"(num\_ways(\"3\")) +
\"0\"(num\_ways(\"03\")) =\> no way to decode \"00\" = 0 + 0

num\_ways (\"103\") =\> \"10\"(num\_ways(\"3\")) +
\"1\"(num\_ways(\"03\")) =\> num\_ways\[i+2\] + num\_ways\[i+1\](= 0 in
this case)

num\_ways (\"1003\") =\> \"10\"(num\_ways(\"03\")) +
\"1\"(num\_ways(\"003\")) =\> same eq = 0(no way to decode \"03\") +
0(no way to decode 003)

Therefore, if i = \'0\', let memo\[i\] = 0, also implements for a string
where the ith character == \'0\', string\[i:end\] can be decoded in 0
ways.

\"\"\"

\*/

// public class Solution {

public int numDecodings(String s) {

int n = s.length();

if (n == 0) return 0;

int\[\] memo = new int\[n+1\];

memo\[n\] = 1;

memo\[n-1\] = s.charAt(n-1) != \'0\' ? 1 : 0;

for (int i = n - 2; i \>= 0; i\--)

if (s.charAt(i) == \'0\') continue;

else memo\[i\] = (Integer.parseInt(s.substring(i,i+2))\<=26) ?
memo\[i+1\]+memo\[i+2\] : memo\[i+1\];

return memo\[0\];

}

// }

/\*

Thank you so much for this clean and intuitive solution!!

I wrote some notes for myself reference, hope it might help someone to
understand this solution.

dp\[i\]: represents possible decode ways to the ith char(include i),
whose index in string is i-1

Base case: dp\[0\] = 1 is just for creating base; dp\[1\], when there\'s
one character, if it is not zero, it can only be 1 decode way. If it is
0, there will be no decode ways.

Here only need to look at at most two digits before i, cuz biggest valid
code is 26, which has two digits.

For dp\[i\]: to avoid index out of boundry, extract substring of
(i-1,i)- which is the ith char(index in String is i-1) and
substring(i-2, i)

First check if substring (i-1,i) is 0 or not. If it is 0, skip it,
continue right to check substring (i-2,i), cuz 0 can only be decode by
being together with the char before 0.

Second, check if substring (i-2,i) falls in 10\~26. If it does, means
there are dp\[i-2\] more new decode ways.

Time: should be O(n), where n is the length of String

Space: should be O(n), where n is the length of String

\*/

public int **numDecodings\_v2**(String s) {

// this is one DP question, so create DP matrxi first

int\[\] dp = new int\[s.length()+1\];

// base case

dp\[0\]=1;

// for only one char, if first char is 0, which is not in the mapping
list, so return 0, otherwise return 1

dp\[1\]=s.charAt(0)==\'0\'?0:1;

int m=s.length();

for (int i = 2; i \<=m ; i++) {

int digitOne=Integer.valueOf(s.substring(i-1,i));

int digitTwo=Integer.valueOf(s.substring(i-2,i));

if(digitOne\>=1){

dp\[i\] = dp\[i\] +dp\[i-1\]; // add one to DP as take this single digit
into account

}

if(digitTwo\>=10 && digitTwo\<=26){

dp\[i\] = dp\[i\] + dp\[i-2\];

}

}

return dp\[m\];

}

}

\[DP\]

class Solution {

public int coinChange(int\[\] coins, int amount) {

// this is one DP problem, so create matrix for number of fewest numbers
of coins to form the

int\[\] dp = new int\[amount+1\]; // index of array is the amount to be
calculated

Arrays.fill(dp,amount+1); // fill DP with \*invalid\* value so we can
update it to valid one late

//base case

dp\[0\]=0;

for(int i=0;i\<=amount;i++){ //\[!!!\] should be \"\<=\", rather than
\"\<\"

for(int j=0;j\<coins.length;j++){

// if current coin is not greater than i (current amount to calculate
fewest number)

if(coins\[j\]\<=i){

// two options, do not take current change OR take current change

dp\[i\] = Math.min(dp\[i\], 1+dp\[i-coins\[j\]\]);

}

}

}

// if dp\[amount\] \> amount, it means it\'s amount+1, which is invalid

return dp\[amount\] \> amount ? -1:dp\[amount\];

}

}

**[\[Recursive\]]{.underline}**

**[Combination sum II]{.underline}**

Each number in candidates may only be used **once** in the combination.

Example 1:

Input: candidates = \[10,1,2,7,6,1,5\], target = 8,

A solution set is:

\[

\[1, 7\],

\[1, 2, 5\],

\[2, 6\],

\[1, 1, 6\]

\]

class Solution {

public List\<List\<Integer\>\> combinationSum2(int\[\] candidates, int
target) {

List\<List\<Integer\>\> result = new ArrayList\<\>();

Arrays.sort(candidates); // here is key to make array increasing

findCombination(candidates,0,target,new ArrayList\<\>(),result);

return result;

}

public void findCombination(int\[\] candidates, int idx, int target,
List\<\> current, List\<List\<\>\> result){

//base case

if(target == 0){

// found correct combination

result.add(current);

return; // should return right away after add

}

// base case 2

if(target\<0){

// last element lead to combination\>target

return;

}

for(int i=idx;i\<candidates.length;i++){

// loop to try combination by DFS

if(i==idx \|\| candidates\[i\]!=candidates\[i-1\]){

// here is key for \"non dup element\"

// as first loop is always unique, no dup

// for non first loop, check it with previous value

current.add(candidates\[i\]); // Not same as previous one

findCombination(candidates,i+1, target-candidates\[i\], current,
result); // here will DFS try to keep on adding new element to current

current.remove(candidates.length-1);// when above line returned, it
means last element is too big

}

}

}

}

**[reverse integer]{.underline}**
---------------------------------

class Solution {

public int reverse(int x) {

long res = 0;

while (x != 0) {

res \*= 10;

res += x % 10;

x /= 10;

}

return (int)res == res ? (int)res : 0;

}

}

public class Solution {

public int reverse(int x) {

long result =0;

while(x != 0)

{

result = (result\*10) + (x%10);

if(result \> Integer.MAX\_VALUE) return 0;

if(result \< Integer.MIN\_VALUE) return 0;

x = x/10;

}

return (int)result;

}

}

**Find median of two sorted array**

\<1\> Set imin = 0, imax = m, then start searching in \[imin, imax\]

\<2\> Set i = (imin + imax)/2, j = (m + n + 1)/2 - i

\<3\> Now we have len(left\_part)==len(right\_part). And there are only
3 situations

that we may encounter:

\<a\> B\[j-1\] \<= A\[i\] and A\[i-1\] \<= B\[j\]

Means we have found the object \`i\`, so stop searching.

\<b\> B\[j-1\] \> A\[i\]

Means A\[i\] is too small. We must \`ajust\` i to get \`B\[j-1\] \<=
A\[i\]\`.

Can we \`increase\` i?

Yes. Because when i is increased, j will be decreased.

So B\[j-1\] is decreased and A\[i\] is increased, and \`B\[j-1\] \<=
A\[i\]\` may

be satisfied.

Can we \`decrease\` i?

\`No!\` Because when i is decreased, j will be increased.

So B\[j-1\] is increased and A\[i\] is decreased, and B\[j-1\] \<=
A\[i\] will

be never satisfied.

So we must \`increase\` i. That is, we must ajust the searching range to

\[i+1, imax\]. So, set imin = i+1, and goto \<2\>.

\<c\> A\[i-1\] \> B\[j\]

Means A\[i-1\] is too big. And we must \`decrease\` i to get
\`A\[i-1\]\<=B\[j\]\`.

That is, we must ajust the searching range to \[imin, i-1\].

So, set imax = i-1, and goto \<2\>.

When the object i is found, the median is:

max(A\[i-1\], B\[j-1\]) (when m + n is odd)

or (max(A\[i-1\], B\[j-1\]) + min(A\[i\], B\[j\]))/2 (when m + n is
even)

Number of distinct Islands

private static int rows, cols;

# deleted 2-D array due to hexo error

public int numDistinctIslands(int\[\]\[\] grid) {

cols = grid\[0\].length;

rows = grid.length;

Set\<String\> uniqueShapes = new HashSet\<\>(); // Unique shpes.

StringBuilder shape;

for (int i = 0; i \< rows; i++) {

for (int j = 0; j \< cols; j++) {

if (grid\[i\]\[j\] == 1) {

grid\[i\]\[j\] = 0; // mark it as \'visited\'

shape = new StringBuilder(\"s\"); //\'s\' indicate Start

dfsTraversal(i, j, grid, shape);

uniqueShapes.add(shape.toString());

}

}

}

return uniqueShapes.size();

}

private static void dfsTraversal(int x, int y, int\[\]\[\] matrix,
StringBuilder shape) {

for (int i = 0; i \< directions.length; i++) {

int nx = x + directions\[i\]\[0\];

int ny = y + directions\[i\]\[1\];

if (nx \>= 0 && ny \>= 0 && nx \< rows && ny \< cols) {

if (matrix\[nx\]\[ny\] == 1) {

matrix\[nx\]\[ny\] = 0; // mark as \'visited\'

shape.append(i);

dfsTraversal(nx, ny, matrix, shape);

}

}

}

shape.append(\"\_\");

}

//=======

class Solution {
# deleted 2-D array due to hexo error

public int numDistinctIslands(int\[\]\[\] grid) {

Set\<String\> set= new HashSet\<\>();

int res=0;

for(int i=0;i\<grid.length;i++){

for(int j=0;j\<grid\[0\].length;j++){

if(grid\[i\]\[j\]==1) {

StringBuilder sb= new StringBuilder();

helper(grid,i,j,0,0, sb);

String s=sb.toString();

if(!set.contains(s)){

res++;

set.add(s);

}

}

}

}

return res;

}

public void helper(int\[\]\[\] grid,int i,int j, int xpos, int
ypos,StringBuilder sb){

grid\[i\]\[j\]=0;

sb.append(xpos+\"\"+ypos);

for(int\[\] dir : dirs){

int x=i+dir\[0\];

int y=j+dir\[1\];

if(x\<0 \|\| y\<0 \|\| x\>=grid.length \|\| y\>=grid\[0\].length \|\|
grid\[x\]\[y\]==0) continue;

helper(grid,x,y,xpos+dir\[0\],ypos+dir\[1\],sb);

}

}

}

UPDATE: We can use direction string instead of using number string in
set.

Below is \@wavy code using direction string.

public int numDistinctIslands(int\[\]\[\] grid) {

Set\<String\> set = new HashSet\<\>();

for(int i = 0; i \< grid.length; i++) {

for(int j = 0; j \< grid\[i\].length; j++) {

if(grid\[i\]\[j\] != 0) {

StringBuilder sb = new StringBuilder();

dfs(grid, i, j, sb, \"o\"); // origin

grid\[i\]\[j\] = 0;

set.add(sb.toString());

}

}

}

return set.size();

}

private void dfs(int\[\]\[\] grid, int i, int j, StringBuilder sb,
String dir) {

if(i \< 0 \|\| i == grid.length \|\| j \< 0 \|\| j == grid\[i\].length

\|\| grid\[i\]\[j\] == 0) return;

sb.append(dir);

grid\[i\]\[j\] = 0;

dfs(grid, i-1, j, sb, \"u\");

dfs(grid, i+1, j, sb, \"d\");

dfs(grid, i, j-1, sb, \"l\");

dfs(grid, i, j+1, sb, \"r\");

sb.append(\"b\"); // back

}

-   In a **complete** binary tree every level, *except possibly the
    > last*, is completely filled, and all nodes in the last level are
    > as far left as possible. It can have between 1 and 2*^h^* nodes at
    > the last level
    > *h*.[^\[18\]^](https://en.wikipedia.org/wiki/Binary_tree#cite_note-complete_binary_tree-18)
    > An alternative definition is a perfect tree whose rightmost leaves
    > (perhaps all) have been removed. Some authors use the term
    > **complete** to refer instead to a perfect binary tree as defined
    > below, in which case they call this type of tree (with a possibly
    > not filled last level) an **almost complete** binary tree or
    > **nearly complete** binary
    > tree.^[\[19\]](https://en.wikipedia.org/wiki/Binary_tree#cite_note-almost_complete_binary_tree-19)[\[20\]](https://en.wikipedia.org/wiki/Binary_tree#cite_note-nearly_complete_binary_tree-20)^
    > A complete binary tree can be efficiently represented using an
    > array.[^\[18\]^](https://en.wikipedia.org/wiki/Binary_tree#cite_note-complete_binary_tree-18)

> ![](media/image1.png){width="2.2916666666666665in"
> height="1.1944444444444444in"}
>
> A complete binary tree (that is not full)

-   A **perfect** binary tree is a binary tree in which all interior
    > nodes have two children *and* all leaves have the same *depth* or
    > same
    > *level*.[^\[21\]^](https://en.wikipedia.org/wiki/Binary_tree#cite_note-21)
    > An example of a perfect binary tree is the (non-incestuous)
    > [ancestry chart](https://en.wikipedia.org/wiki/Ancestry_chart) of
    > a person to a given depth, as each person has exactly two
    > biological parents (one mother and one father). Provided the
    > ancestry chart always displays the mother and the father on the
    > same side for a given node, their sex can be seen as an analogy of
    > left and right children, *children* being understood here as an
    > algorithmic term. A perfect tree is therefore always complete but
    > a complete tree is not necessarily perfect.

Heap Tree is a special balanced binary tree data structure where root
node is compared with its children and averaged accordingly. There are
two type of trees, min heap tree and map heap tree.

For Min heap tree, it's parent is either smaller or equals its childers.

### Get Tree Height

static int getHeight\_recursive(TreeNode root){

if(root==null){

return 0;

}

return
Math.max(getHeight\_recursive(root.left),getHeight\_recursive(root.right))+1;
//\[!!!!!\] Here is the key point, it should add \"1\" at last

}

/\*

The basic idea:

1\. traverse layer by layer

2\. For each layer, firslty get number of element,

3\. Then add its left & right child for each element

4\. Increase height once all element of current layer finished

\*/

static int getHeight\_Iteratively(TreeNode root) {

int height=0;

Stack\<TreeNode\> stack=new Stack\<\>();

stack.add(root);

while(!stack.isEmpty()){

int numberOfSibling=stack.size();

// loop in all element in this layer till none is left

while(numberOfSibling\-- \>0){

root = stack.pop();

// add current element\'s children

if(root.left!=null) stack.push(root.left);

if(root.right!=null) stack.push(root.right);

}

height++;

}

return height;

}

InvertTree
----------

package algo;

public class TreeInvertBST {

public static void main(String\[\] args) {

System.out.printf(\"===start===\");

TreeNode root = invertTree(TreeNode.buildBSTTree());

System.out.printf(\"invert tree: \"+ root);

}

static TreeNode invertTree(TreeNode root){

if(root==null) return null;

**TreeNode tmpLeft = root.left;**

**root.left=invertTree(root.right);**

**root.right=invertTree(tmpLeft);**

return root;

}

}

### **[Number of islands]{.underline}**

static int numberOfIslands(char\[\]\[\] grid){

int number = 0;

if(grid==null \|\| grid.length \<0 \|\| grid\[0\].length\<0 ) {

return 0;

}

for (int i = 0; i \< grid.length; i++) {

for (int j = 0; j \<grid\[i\].length ; j++) {

if(grid\[i\]\[j\]==\'1\') {

// DFS to clear adjacent \"1\" to avoid dup counting

DFS(grid, i, j);

++number;

}

}

}

return number;

}

// the main purpose of calling DFS is to set "0" for all adjacent "1"
cells. As they all together to form one island

static void DFS(char\[\]\[\] grid, int x, int y){

//edge case

if(grid==null \|\| x\<0 \|\| x \>= grid.length \|\| y\<0 \|\|
y\>=grid\[0\].length **\|\| grid\[x\]\[y\]==\'0\') { //\[!!!!\] should
\>= length, not \"\>\"**

// if(grid==null \|\| x\<0 \|\| x \> grid.length \|\| y\<0 \|\|
y\>grid\[0\].length \|\| grid\[x\]\[y\]==0) {

// return if cursor node is NOT 1

return;

}

// means current cursor node is \"1\"

grid\[x\]\[y\]=\'0\'; // mark this cell as visited

// check all adjacent cells

DFS(grid, x-1, y);

DFS(grid, x+1, y);

DFS(grid, x, y-1);

DFS(grid, x, y+1);

}

\-\-\-\-\-\-\-\--

**Is a same tree:**

static boolean isSameTree(TreeNode tree1, TreeNode tree2) {

// check base case, null checking

if(tree1==null \|\| tree2 ==null){

return tree1 == tree2; // true when both null, false when only one is
null

}

/\* same tress should be :

1\. node data is same

2\. left sub tree is same

4\. right sub tree is same

\*/

return tree1.val==tree2.val && isSameTree(tree1.left,tree2.left) &&
isSameTree(tree1.right,tree2.right);

}

**Search BST**

public static TreeNode searchBST(TreeNode root, int val) {

if(root==null){

return null;

}

if(root.val==val){

return root;

}else if(val \> root.val){

return searchBST(root.right, val);

} else {

return searchBST(root.left,val);

}

}

public static TreeNode searchBST\_Iterative(TreeNode root, int val) {

// recursive approach means recursively assgin/update variables

while(root != null && root.val != val){

root = val\<root.val? root.left:root.right;

}

return root;

}

}

**Tree Traverse:**

static public List\<Integer\> **inorderTraversal\_better**(TreeNode
root) {

List\<Integer\> listRtn = new ArrayList\<\>();

// for inorder trave iteratively we\'ll push/pop stacks

Stack\<TreeNode\> stack = new Stack\<\>();

// to determine when to push stack

// for inorder traverse, to push left first, then pop root, then last
right

while(root!=null \|\| !stack.empty()) {

while(root!=null){

stack.push(root);

// keep on assign left to root for in order traverse

root=root.left;

}

root = stack.pop(); // pop up value of root

listRtn.add(root.val);

root=root.right;

}

return listRtn;

}

/\*

This one is more intuitive

\*/

static public List\<Integer\> **preorderTraversal\_better**(TreeNode
root) {

List\<Integer\> listRtn = new ArrayList\<\>();

Stack\<TreeNode\> stack = new Stack\<\>();

stack.push(root);

while (!stack.empty()) {

root = stack.pop(); // pop up value of root

if (root != null) {

listRtn.add(root.val);

stack.push(root.right);

stack.push(root.left);

}

}

return listRtn;

}

static List\<Integer\> **postOrderTraversal\_stack\_better**(TreeNode
node) {

List\<Integer\> list = new ArrayList\<\>();

if(node==null) {

return list;

}

Stack\<TreeNode\> stack = new Stack\<\>();

stack.push(node);

while(!stack.isEmpty()){

node= stack.pop();

list.add(0, node.val); //\[!!!!!!!!!!\] here is key logic, add item at
postion \"0\" means at the begining

if(node.left!=null) stack.push(node.left);

if(node.right!=null) stack.push(node.right);

}

return list;

}

binaryTreeIsBST

/\*

The key logic are:

1\. assign two boundaries (lower , upper) for each node,

2\. update upper to current node for its left child and lower for its
right child

3\. recursively check each node

\*/

static boolean binaryTreeIsBST(TreeNode node, int lower, int upper){

// for recursive, base case

// Number 1: base case is null return true

if(node==null) return true;

// Number 2: check data

if(node.val \< lower \|\| node.val\>upper) {

System.out.printf(\"%s failed in BST check \[%d,%d\]: \", node,
lower,upper);

return false;

}

// for left child node, it\'s value should between current\'s node\'s
lower boundary and current node\'s value

// for right child node, it\'s value should between current node\'s
value and current\'s node\'s upper boundary

return binaryTreeIsBST(node.left,lower,node.val) &&
binaryTreeIsBST(node.right,node.val, upper);

}

**Iteratively check binary tree is BST**: (use inOrder search , only
replace list.add with checking pre)

public boolean isValidBST(TreeNode root) {

if (root == null) return true;

Stack\<TreeNode\> stack = new Stack\<\>();

TreeNode pre = null;

while (root != null \|\| !stack.isEmpty()) {

while (root != null) {

stack.push(root);

root = root.left;

}

root = stack.pop();

**if(pre != null && root.val \<= pre.val) return false;**

**pre = root;**

root = root.right;

}

return true;

}

======

**Kth smallest element**

public int kthSmallest(TreeNode root, int k) {

Stack\<TreeNode\> stack = new Stack\<\>();

while(root != null \|\| !stack.isEmpty()) {

while(root != null) {

stack.push(root);

root = root.left;

}

root = stack.pop();

**if(\--k == 0) break;**

root = root.right;

}

return root.val;

}

contrapositive

contradiction

cases

induction

Interview tips:

-   Do not silent, ask" can I think for a second "

-   Think out loud

-   Use examples

-   Ask " does that sound a good strategy" rather than write code right
    > away

-   Better naming variable. For dynamic programing. If you use memoized
    > solution, better to name array as "// memorized solitoon memo\[\]

编辑距离问题就是给我们两个字符串 s1 和 s2，只能用三种操作，让我们把 s1
变成 s2，求最少的操作数。需要明确的是，不管是把 s1 变成 s2
还是反过来，结果都是一样的，所以后文就以 s1 变成 s2 举例。

前文「」说过，解决两个字符串的动态规划问题，一般都是用两个指针 i,j
分别指向两个字符串的最后，然后一步步往前走，缩小问题的规模。

一、动态规划解法

动态规划的核心设计思想是数学归纳法

总结一下动态规划的设计流程：

首先明确 dp
数组所存数据的含义。这步很重要，如果不得当或者不够清晰，会阻碍之后的步骤。

然后根据 dp 数组的定义，运用数学归纳法的思想，假设 \$dp\[0\...i-1\]\$
都已知，想办法求出 \$dp\[i\]\$，一旦这一步完成，整个题目基本就解决了。

但如果无法完成这一步，很可能就是 dp 数组的定义不够恰当，需要重新定义 dp
数组的含义；或者可能是 dp
数组存储的信息还不够，不足以推出下一步的答案，需要把 dp
数组扩大成二维数组甚至三维数组。

最后想一想问题的 base case 是什么，以此来初始化 dp
数组，以保证算法正确运行。

最长递增子序列（Longest Increasing Subsequence，简写
LIS）是比较经典的一个问题，比较容易想到的是动态规划解法，时间复杂度
O(N\^2)，

我们的定义是这样的：dp\[i\] 表示以 nums\[i\]
这个数结尾的最长递增子序列的长度。

根据刚才我们对 dp 数组的定义，现在想求 dp\[5\] 的值，也就是想求以
nums\[5\] 为结尾的最长递增子序列。

nums\[5\] = 3，既然是递增子序列，我们只要找到前面那些结尾比 3
小的子序列，然后把 3
接到最后，就可以形成一个新的递增子序列，而且这个新的子序列长度加一。

当然，可能形成很多种新的子序列，但是我们只要最长的，把最长子序列的长度作为
dp\[5\] 的值即可。

还有一个细节问题，dp 数组应该全部初始化为
1，因为子序列最少也要包含自己，所以长度最小为
1。下面我们看一下完整代码：

public int **[lengthOfLIS]{.underline}**(int\[\] nums) {

int\[\] dp = new int\[nums.length\];

// dp 数组全都初始化为 1

Arrays.fill(dp, 1);

for (int i = 0; i \< nums.length; i++) {

for (int j = 0; j \< i; j++) {

if (nums\[i\] \> nums\[j\])

dp\[i\] = Math.max(dp\[i\], dp\[j\] + 1);

}

}

int res = 0;

for (int i = 0; i \< dp.length; i++) {

res = Math.max(res, dp\[i\]);

}

return res;

}

public int lengthOfLIS(int\[\] nums) {

int\[\] top = new int\[nums.length\];

// 牌堆数初始化为 0

int piles = 0;

for (int i = 0; i \< nums.length; i++) {

// 要处理的扑克牌

int poker = nums\[i\];

/\*\*\*\*\* 搜索左侧边界的二分查找 \*\*\*\*\*/

int left = 0, right = piles;

while (left \< right) {

int mid = (left + right) / 2;

if (top\[mid\] \> poker) {

right = mid;

} else if (top\[mid\] \< poker) {

left = mid + 1;

} else {

right = mid;

}

}

/\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*/

// 没找到合适的牌堆，新建一堆

if (left == piles) piles++;

// 把这张牌放到牌堆顶

top\[left\] = poker;

}

// 牌堆数就是 LIS 长度

return piles;

}

至此，二分查找的解法也讲解完毕。

这个解法确实很难想到。首先涉及数学证明，谁能想到按照这些规则执行，就能得到最长递增子序列呢？其次还有二分查找的运用，要是对二分查找的细节不清楚，给了思路也很难写对

/\* Dynamic Programming Java implementation of LIS problem \*/

class LIS

{

/\* lis() returns the length of the longest increasing

subsequence in arr\[\] of size n \*/

static int lis(int arr\[\],int n)

{

int lis\[\] = new int\[n\];

int i,j,max = 0;

/\* Initialize LIS values for all indexes \*/

for ( i = 0; i \< n; i++ )

lis\[i\] = 1;

/\* Compute optimized LIS values in bottom up manner \*/

for ( i = 1; i \< n; i++ )

for ( j = 0; j \< i; j++ )

if ( arr\[i\] \> arr\[j\] && lis\[i\] \< lis\[j\] + 1)

lis\[i\] = lis\[j\] + 1;

/\* Pick maximum of all LIS values \*/

for ( i = 0; i \< n; i++ )

if ( max \< lis\[i\] )

max = lis\[i\];

return max;

}

public static void main(String args\[\])

{

int arr\[\] = { 10, 22, 9, 33, 21, 50, 41, 60 };

int n = arr.length;

System.out.println(\"Length of lis is \" + lis( arr, n ) + \"\\n\" );

}

}

/\*This code is contributed by Raja

\-\-\-\--

Find number of days between two given dates

Given two dates, find total number of days between them. The count of
days must be calculated in O(1) time and O(1) auxiliary space.

Examples:

Input: dt1 = {10, 2, 2014}

dt2 = {10, 3, 2015}

Output: 393

dt1 represents \"10-Feb-2014\" and dt2 represents \"10-Mar-2015\"

The difference is 365 + 28

Input: dt1 = {10, 2, 2000}

dt2 = {10, 3, 2000}

Output: 29

Note that 2000 is a leap year

Input: dt1 = {10, 2, 2000}

dt2 = {10, 2, 2000}

Output: 0

Both dates are same

Input: dt1 = {1, 2, 2000};

dt2 = {1, 2, 2004};

Output: 1461

Number of days is 365\*4 + 1

One Naive Solution is to start from dt1 and keep counting days till dt2
is reached. This solution requires more than O(1) time.

A Better and Simple solution is to count total number of days before dt1
from i.e., total days from 00/00/0000 to dt1, then count total number of
days before dt2. Finally return the difference between two counts.

Let the given two dates be \"1-Feb-2000\" and \"1-Feb-2004\"

dt1 = {1, 2, 2000};

dt2 = {1, 2, 2004};

Count number of days before dt1. Let this count be n1.

Every leap year adds one extra day (29 Feb) to total days.

n1 = 2000\*365 + 31 + 1 + Number of leap years

Count of leap years for a date \'d/m/y\' can be calculated

using following formula:

Number leap years

= y/4 - y/100 + y/400 if m \> 2

= (y-1)/4 - (y-1)/100 + (y-1)/400 if m \<= 2

All above divisions must be done using integer arithmetic

so that the remainder is ignored.

For 01/01/2000, leap year count is 1999/4 - 1999/100

\+ 1999/400 which is 499 - 19 + 4 = 484

Therefore n1 is 2000\*365 + 31 + 1 + 484

Similarly, count number of days before dt2. Let this

count be n2.

Finally return n2-n1

------

// Java program two find number of

// days between two given dates

class GFG

{

// A date has day \'d\', month \'m\' and year \'y\'

static class Date

{

int d, m, y;

public Date(int d, int m, int y)

{

this.d = d;

this.m = m;

this.y = y;

}

};

// To store number of days in

// all months from January to Dec.

static int monthDays\[\] = {31, 28, 31, 30, 31, 30,

31, 31, 30, 31, 30, 31};

// This function counts number of

// leap years before the given date

static int countLeapYears(Date d)

{

int years = d.y;

// Check if the current year needs to be considered

// for the count of leap years or not

if (d.m \<= 2)

{

years\--;

}

// An year is a leap year if it is a multiple of 4,

// multiple of 400 and not a multiple of 100.

return years / 4 - years / 100 + years / 400;

}

// This function returns number

// of days between two given dates

static int getDifference(Date dt1, Date dt2)

{

// COUNT TOTAL NUMBER OF DAYS BEFORE FIRST DATE \'dt1\'

// initialize count using years and day

int n1 = dt1.y \* 365 + dt1.d;

// Add days for months in given date

for (int i = 0; i \< dt1.m - 1; i++)

{

n1 += monthDays\[i\];

}

// Since every leap year is of 366 days,

// Add a day for every leap year

n1 += countLeapYears(dt1);

// SIMILARLY, COUNT TOTAL NUMBER OF DAYS BEFORE \'dt2\'

int n2 = dt2.y \* 365 + dt2.d;

for (int i = 0; i \< dt2.m - 1; i++)

{

n2 += monthDays\[i\];

}

n2 += countLeapYears(dt2);

// return difference between two counts

return (n2 - n1);

}

// Driver code

public static void main(String\[\] args)

{

Date dt1 = new Date(1, 2, 2000);

Date dt2 = new Date(1, 2, 2004);

System.out.println(\"Difference between two dates is \" +

getDifference(dt1, dt2));

}

}

Last Edit: 6 hours ago

karansingh1559

karansingh1559

179

I am trying to compile a list of DP questions commonly asked in
interviews. This will help me and others trying to get better at DP. The
list will be sorted by difficulty. If you\'ve come across DP questions,
do mention them in the comments.

EASY:

121\. Best time to buy and sell stock

198\. House Robber

256\. Paint House

MEDIUM:

63\. Unique Paths II

64\. Minimum Path Sum

91\. Decode Ways

139\. Word Break

221\. Maximal Square

300\. Longest Increasing Subsequence

322\. Coin Change

464\. Can I Win

474\. Ones and Zeroes

516\. Longest Palindromic Subsequence

698\. Partition to K Equal Sum Subsets

787\. Cheapest Flights Within K Stops

1027\. Longest Arithmetic Sequence

1049\. Last Stone Weight II

1105\. Filling Bookcase Shelves

1143\. Longest Common Subsequence

1155\. Dice Roll Sum

HARD:

32\. Longest Valid Parantheses

44\. Wildcard Matching

72\. Edit Distance

123\. Best Time to Buy and Sell Stock III

312\. Burst Balloons

1000\. Minimum Cost to Merge Stones

1335\. Minimum Difficulty of a Job Schedule

dynamic programming

**Minimum (Maximum) Path to Reach a Target**

**Generate problem statement for this pattern**

Statement

Given a target find minimum (maximum) cost / path / sum to reach the
target.

Approach

Choose minimum (maximum) path among all possible paths before the
current state, then add value for the current state.

routes\[i\] = min(routes\[i-1\], routes\[i-2\], \... , routes\[i-k\]) +
cost\[i\]

Generate optimal solutions for all values in the target and return the
value for the target.

for (int i = 1; i \<= target; ++i) {

for (int j = 0; j \< ways.size(); ++j) {

if (ways\[j\] \<= i) {

dp\[i\] = min(dp\[i\], dp\[i - ways\[j\]\]) + cost / path / sum;

}

}

}

return dp\[target\]

Similar Problems

746\. **[Min Cost Climbing Stairs Easy]{.underline}**

for (int i = 2; i \<= n; ++i) {

dp\[i\] = min(dp\[i-1\], dp\[i-2\]) + (i == n ? 0 : cost\[i\]);

}

return dp\[n\]

64\. Minimum Path Sum Medium

for (int i = 1; i \< n; ++i) {

for (int j = 1; j \< m; ++j) {

grid\[i\]\[j\] = min(grid\[i-1\]\[j\], grid\[i\]\[j-1\]) +
grid\[i\]\[j\];

}

}

return grid\[n-1\]\[m-1\]

322\. Coin Change Medium

for (int j = 1; j \<= amount; ++j) {

for (int i = 0; i \< coins.size(); ++i) {

if (coins\[i\] \<= j) {

dp\[j\] = min(dp\[j\], dp\[j - coins\[i\]\] + 1);

}

}

}

Tree
====

Find minimum path
-----------------

class Solution {

public int minDepth(TreeNode root) {

if(root == null) return 0; // base case

int left = minDepth(root.left); // get depth of left

int right = minDepth(root.right); // get depth of right

if(root.left == null) return right + 1; // leaf nodes are in right
subtree

if(root.right == null) return left + 1; // leaf nodes are in left
subtree

// if left/right subtrees both contains leaf nodes

return Math.min(left, right) + 1;

}

}

Get min depth in Iterative approach

public int minDepth(TreeNode root) {

if(root == null)

return 0;

Queue\<TreeNode\> que = new LinkedList();

int level =1;

que.add(root);

while(!que.isEmpty()){

int size = que.size();

while(size\>0){

TreeNode node =que.poll();

if(node.left == null && node.right ==null)

return level;

if(node.left != null)

que.add(node.left);

if(node.right != null)

que.add(node.right);

size\--;

}

level++;

}

return level;

}

=================

two solutions with explanation: DFS & BFS:

/\*\* Solution 1: DFS

\* Key point:

\* if a node only has one child -\> MUST return the depth of the side
with child, i.e. MAX(left, right) + 1

\* if a node has two children on both side -\> return min depth of two
sides, i.e. MIN(left, right) + 1

\* \*/

public int minDepth(TreeNode root) {

if (root == null) {

return 0;

}

int left = minDepth(root.left);

int right = minDepth(root.right);

if (left == 0 \|\| right == 0) {

return Math.max(left, right) + 1;

}

else {

return Math.min(left, right) + 1;

}

}

/\*\* Solution 2: BFS level order traversal \*/

public int minDepth2(TreeNode root) {

if (root == null) {

return 0;

}

Queue\<TreeNode\> queue = new LinkedList\<\>();

queue.offer(root);

int level = 1;

while (!queue.isEmpty()) {

int size = queue.size();

for (int i = 0; i \< size; i++) {

TreeNode curNode = queue.poll();

if (curNode.left == null && curNode.right == null) {

return level;

}

if (curNode.left != null) {

queue.offer(curNode.left);

}

if (curNode.right != null) {

queue.offer(curNode.right);

}

}

level++;

}

return level;

}

Preorder Traversal

In preorder traversal, we traverse the root first, then the left and
right subtrees.

We can simply implement preorder traversal using recursion:

public void traversePreOrder(Node node) {

if (node != null) {

visit(node.value);

traversePreOrder(node.left);

traversePreOrder(node.right);

}

}

We can also implement preorder traversal without recursion.

To implement an iterative preorder traversal, we\'ll need a Stack, and
we\'ll go through these steps:

Push root in our stack

While stack is not empty

Pop current node

Visit current node

Push right child, then left child to stack

public void traversePreOrderWithoutRecursion() {

Stack\<Node\> stack = new Stack\<Node\>();

Node current = root;

stack.push(root);

while(!stack.isEmpty()) {

current = stack.pop();

visit(current.value);

if(current.right != null) {

stack.push(current.right);

}

if(current.left != null) {

stack.push(current.left);

}

}

}

Convert Sorted List to Binary Search Tree

Medium

1503

79

Add to List

Share

Given a singly linked list where elements are sorted in ascending order,
convert it to a height balanced BST.

For this problem, a height-balanced binary tree is defined as a binary
tree in which the depth of the two subtrees of *every* node never differ
by more than 1.

Example:

Given the sorted linked list: \[-10,-3,0,5,9\],

One possible answer is: \[0,-3,9,-10,null,5\], which represents the
following height balanced BST:

0

/ \\

-3 9

/ /

-10 5

**breadth first search**

First of all, let\'s reuse the algorithm from above, adapted to the new
structure:

public static \<T\> Optional\<Node\<T\>\> search(T value, Node\<T\>
start) {

Queue\<Node\<T\>\> queue = new ArrayDeque\<\>();

queue.add(start);

Node\<T\> currentNode;

while (!queue.isEmpty()) {

currentNode = queue.remove();

if (currentNode.getValue().equals(value)) {

return Optional.of(currentNode);

} else {

queue.addAll(currentNode.getNeighbors());

}

}

return Optional.empty();

}

[Binary search]{.underline} 
===========================

**分析二分查找的一个技巧是：不要出现 else，而是把所有情况用 else if
写清楚，这样可以清楚地展现所有细节**。

\-\-\-\-\--

Sliding window

In any sliding window based problem we have two pointers. One *right*
pointer whose job is to expand the current window and then we have the
*left* pointer whose job is to contract a given window. At any point in
time only one of these pointers move and the other one remains fixed.

Smallest window contains sub string

public class Solution {

public String minWindow(String s, String t) {

if(s == null \|\| s.length() \< t.length() \|\| s.length() == 0){

return \"\";

}

HashMap\<Character,Integer\> map = new HashMap\<Character,Integer\>();

for(char c : t.toCharArray()){

if(map.containsKey(c)){

map.put(c,map.get(c)+1);

}else{

map.put(c,1);

}

}

int left = 0;

int minLeft = 0;

int minLen = s.length()+1;

int count = 0;

for(int right = 0; right \< s.length(); right++){

if(map.containsKey(s.charAt(right))){

map.put(s.charAt(right),map.get(s.charAt(right))-1);

if(map.get(s.charAt(right)) \>= 0){

count ++;

}

while(count == t.length()){

if(right-left+1 \< minLen){

minLeft = left;

minLen = right-left+1;

}

if(map.containsKey(s.charAt(left))){

map.put(s.charAt(left),map.get(s.charAt(left))+1);

if(map.get(s.charAt(left)) \> 0){

count \--;

}

}

left ++ ;

}

}

}

if(minLen\>s.length())

{

return \"\";

}

return s.substring(minLeft,minLeft+minLen);

}

}

\--

public static String minWindowOp(String s, String t) {

int \[\] map = new int\[128\];//map to track number of occurrence of
each character of sub string

for (char c : t.toCharArray()) {

map\[c\]++;

}

int start = 0, end = 0, minStart = 0, minLen = Integer.MAX\_VALUE,
counter = t.length();

// counter is number of distinct chars in sub string

while (end \< s.length()) {

final char c1 = s.charAt(end);// walk through each char in source string

if (map\[c1\] \> 0) {

counter\--; // if cached char number greater than 0, decrease counter

}

map\[c1\]\--;//decrease cached char number, for chars not in substring,
it will be negative

end++; //move right pointer

while (counter == 0) { //counter is zero means all chars found

if (minLen \> end - start) { //to find and cache minimum sliding window
length and minimum start

minLen = end - start;

minStart = start;

}

final char c2 = s.charAt(start);

map\[c2\]++;// A is -2， B is 1

if (map\[c2\] \> 0) {

counter++; //if current char exist in cache, increase counter, otherwise
keep counter zero

}

start++;

}

}

return minLen == Integer.MAX\_VALUE ? \"\" : s.substring(minStart,
minStart + minLen);

}

\-\-\-\-\--

I agree with your code, but I prefer this code when count == t.length(),

class Solution {

public String minWindow(String s, String t) {

// corner case

if(s == null \|\| t == null \|\| s.length() == 0 \|\| t.length() == 0
\|\| s.length() \< t.length()) return \"\";

// construct model

int minLeft = 0;

int minRight = 0;

int min = s.length();

boolean flag = false;

Map\<Character, Integer\> map = new HashMap\<\>();

int count = t.length(); // the number of characters that I need to match

for(char c : t.toCharArray()) map.put(c, map.getOrDefault(c, 0) + 1);

// unfixed sliding window, 2 pointers

int i = 0;

int j = 0;

while(j \< s.length()){

char c = s.charAt(j);

if(map.containsKey(c)){

map.put(c, map.get(c) - 1);

if(map.get(c) \>= 0) count\--; // if still unmatched characters, then
count\--

}

// if found a susbtring

while(count == 0 && i \<= j){

// update global min

flag = true;

int curLen = j + 1 - i;

if(curLen \<= min){

minLeft = i;

minRight = j;

min = curLen;

}

// shrink left pointer

char leftC = s.charAt(i);

if(map.containsKey(leftC)){

map.put(leftC, map.get(leftC) + 1);

if(map.get(leftC) \>= 1) count++;

}

i++;

}

j++;

}

return flag == true ? s.substring(minLeft, minRight + 1): \"\";

}

}

First part: when the right pointer is getting incremented we are
decrementing the map count of char if it\'s part of \'t\' string. When
we see that the map count of that char after decrementing is
positive/zero means that the right ptr has found a useful char and hence
we increment the \'count\' variable (which is keeping track of the
number of useful chars)

Second part: when the left pointer is getting incremented we are
essentially making the window smaller and giving back the chars to the
map (i.e. incrementing the map count). If we find that for the
particular char the map count has now become positive means that we
actually gave back a useful char and hence the \'count\' is to be
decremented.

At this point then we again start increasing our window and see each
time if the count has become equal to the number of chars in \'t\'
string.

\-\-\--

Generally, there are following steps:

1.  create a hashmap for each character in t and count their frequency
    > in t as the value of hashmap.

2.  Find the first window in S that contains T. But how? there the
    > author uses the count.

3.  Checking from the leftmost index of the window and to see if it
    > belongs to t. The reason we do so is that we want to shrink the
    > size of the window.\
    > 3-1) If the character at leftmost index does not belong to t, we
    > can directly remove this leftmost value and update our window(its
    > minLeft and minLen value)\
    > 3-2) If the character indeed exists in t, we still remove it, but
    > in the next step, we will increase the right pointer and expect
    > the removed character. If find so, repeat step 3.

public String minWindow(String s, String t) {

HashMap\<Character, Integer\> map = new HashMap();

for(char c : t.toCharArray()){

if(map.containsKey(c)){

map.put(c, map.get(c)+1);

}

else{

map.put(c, 1);

}

}

int left = 0, minLeft=0, minLen =s.length()+1, count = 0;

for(int right = 0; right\<s.length(); right++){

char r = s.charAt(right);

if(map.containsKey(r)){//the goal of this part is to get the first
window that contains whole t

map.put(r, map.get(r)-1);

if(map.get(r)\>=0) count++;//identify if the first window is found by
counting frequency of the characters of t showing up in S

}

while(count == t.length()){//if the count is equal to the length of t,
then we find such window

if(right-left+1 \< minLen){//jsut update the minleft and minlen value

minLeft = left;

minLen = right-left+1;

}

char l = s.charAt(left);

if(map.containsKey(l)){//starting from the leftmost index of the window,
we want to check if s\[left\] is in t. If so, we will remove it from the
window, and increase 1 time on its counter in hashmap which means we
will expect the same character later by shifting right index. At the
same time, we need to reduce the size of the window due to the removal.

map.put(l, map.get(l)+1);

if(map.get(l)\>0) count\--;

}

left++;//if it doesn\'t exist in t, it is not supposed to be in the
window, left++. If it does exist in t, the reason is stated as above.
left++.

}

}

return minLen==s.length()+1?\"\":s.substring(minLeft, minLeft+minLen);

\-\-\-\-\-\-\-\-\-\-\-\-- best solution\-\--

public static String minWindowBetter(String s, String t){

if(s==null\|\|t==null\|s.length()==0\|\|t.length()==0){

return \"\";

}

int left=0,right=0,count=0,min=Integer.MAX\_VALUE;

int pool\[\] = new int\[256\];

String rtn=\"\";

for(int i =0;i\<t.length();i++){

pool\[t.charAt(i)\]++;

}

while(right\<s.length()){

if(pool\[s.charAt(right++)\]\--\>0){//\[!\]

// (a) if(pool\[s.charAt(right++)\]\--\>=0), rather than
if(pool\[right++\]\--\>=0)

// (b) this is \"\>0\", but not \"\>=0\"

count++;

}

while(count==t.length()){

if((right-left)\<min){

min=right-left;

rtn=s.substring(left,right);

}

//shrink window

if(++pool\[s.charAt(left++)\]\>0){

count\--;

}

}

}

return rtn;

}

while(right \< length of s){

> Deincrement characters frequence at right pointer in String s from
> bank
>
> Right \-- (expand window)
>
> If that character was inside of t, increase count
>
> while(count equal to length of t - condition){
>
> Check if right-left less than min, if so, update min and curr string
>
> Increate characters frequences at left pointer in string, s from bank
>
> Left++ (shift window)
>
> If bank\[character at left pointer\]\>=0, then decrease count.

}

**[knapsack 0/1 背包]{.underline}**

用子问题定义状态：即f\[i\]\[v\]表示前i件物品恰放入一个容量为v的背包可以获得的最大价值。则其状态转移方程便是：

f\[i\]\[v\]=max{f\[i-1\]\[v\],f\[i-1\]\[v-c\[i\]\]+w\[i\]}

这个方程非常重要，基本上所有跟背包相关的问题的方程都是由它衍生出来的。所以有必要将它详细解释一下："将前i件物品放入容量为v的背包中"这个子问题，若只考虑第i件物品的策略（放或不放），那么就可以转化为一个只牵扯前i-1件物品的问题。如果不放第i件物品，那么问题就转化为"前i-1件物品放入容量为v的背包中"，价值为f\[i-1\]\[v\]；如果放第i件物品，那么问题就转化为"前i-1件物品放入剩下的容量为v-c\[i\]的背包中"，此时能获得的最大价值就是f\[i-1\]\[v-c\[i\]\]再加上通过放入第i件物品获得的价值w\[i\]。

private static int knapsack01(int\[\] weights, int\[\] value, int quota)
{

// we are using dynamic programming bottom up

// one tab to keep track of value, size is quota + 1

int\[\]\[\] dp = new int\[value.length+1\]\[quota+1\];

// as size is actual size + 1, so here is \"\<=\" , rather than \"\<\"

for(int i=0;i\<=value.length;i++){

for (int j =0;j\<=quota;j++){

//base value

if(i==0 \|\| j==0){

// initilize first line and first column to \'0\'

dp\[i\]\[j\] = 0;

continue;

}

// non zero

if(j\>=weights\[i-1\]){

// current weight not bigger than current quota

// so add it to our backtrack

// get the max one of (1) Not include , (2) include this node

dp\[i\]\[j\]= Math.*max*(dp\[i-1\]\[j\],
dp\[i-1\]\[j-weights\[i-1\]\]+value\[i-1\]);

}else{

// required weight is less than provided, so skip this

dp\[i\]\[j\] = dp\[i-1\]\[j\]; //use value (j) of previous (i-1

}

}

}

return dp\[value.length\]\[quota\];

}

**[KMP 算法]{.underline}**

KMP
算法永不回退txt的指针i，不走回头路（不会重复扫描txt），而是借助dp数组中储存的信息把pat移到正确的位置继续匹配，时间复杂度只需
O(N)，用空间换时间，所以我认为它是一种动态规划算法。

// 暴力匹配（伪码）

int search(String pat, String txt) {

int M = pat.length;

int N = txt.length;

for (int i = 0; i \< N - M; i++) {

int j;

for (j = 0; j \< M; j++) {

if (pat\[j\] != txt\[i+j\])

break;

}

// pat 全都匹配了

if (j == M) return i;

}

// txt 中不存在 pat 子串

return -1;

\-\--

dynamic programming

public class KMP {

private int\[\]\[\] dp;

private String pat;

public KMP(String pat) {

this.pat = pat;

// 通过 pat 构建 dp 数组

// 需要 O(M) 时间

}

public int search(String txt) {

// 借助 dp 数组去匹配 txt

// 需要 O(N) 时间

}

}

为了描述状态转移图，我们定义一个二维 dp 数组，它的含义如下：

dp\[j\]\[c\] = next

0 \<= j \< M，代表当前的状态

0 \<= c \< 256，代表遇到的字符（ASCII 码）

0 \<= next \<= M，代表下一个状态

dp\[4\]\[\'A\'\] = 3 表示：

当前是状态 4，如果遇到字符 A，

pat 应该转移到状态 3

dp\[1\]\[\'B\'\] = 2 表示：

当前是状态 1，如果遇到字符 B，

pat 应该转移到状态 2

根据我们这个 dp 数组的定义和刚才状态转移的过程，我们可以先写出 KMP
算法的 search 函数代码：

public int search(String txt) {

int M = pat.length();

int N = txt.length();

// pat 的初始态为 0

int j = 0;

for (int i = 0; i \< N; i++) {

// 当前是状态 j，遇到字符 txt\[i\]，

// pat 应该转移到哪个状态？

j = dp\[j\]\[txt.charAt(i)\];

// 如果达到终止态，返回匹配开头的索引

if (j == M) return i - M + 1;

}

// 没到达终止态，匹配失败

return -1;

}

for 0 \<= j \< M: \# 状态

for 0 \<= c \< 256: \# 字符

dp\[j\]\[c\] = next

这个 next
状态应该怎么求呢？显然，如果遇到的字符c和pat\[j\]匹配的话，状态就应该向前推进一个，也就是说next
= j + 1，我们不妨称这种情况为状态推进：

如果遇到的字符c和pat\[j\]不匹配的话，状态就要回退（或者原地不动），我们不妨称这种情况为状态重启：

那么，如何得知在哪个状态重启呢？解答这个问题之前，我们再定义一个名字：影子状态（我编的名字），用变量X表示。所谓影子状态，就是和当前状态具有相同的前缀。比如下面这种情况：

当前状态j = 4，其影子状态为X = 2，它们都有相同的前缀
\"AB\"。因为状态X和状态j存在相同的前缀，所以当状态j准备进行状态重启的时候（遇到的字符c和pat\[j\]不匹配），可以通过X的状态转移图来获得最近的重启位置。

比如说刚才的情况，如果状态j遇到一个字符
\"A\"，应该转移到哪里呢？首先状态 4 只有遇到 \"C\" 才能推进状态，遇到
\"A\"
显然只能进行状态重启。状态j会把这个字符委托给状态X处理，也就是dp\[j\]\[\'A\'\]
= dp\[X\]\[\'A\'\]：

int X \# 影子状态

for 0 \<= j \< M:

for 0 \<= c \< 256:

if c == pat\[j\]:

\# 状态推进

dp\[j\]\[c\] = j + 1

else:

\# 状态重启

\# 委托 X 计算重启位置

dp\[j\]\[c\] = dp\[X\]\[c\]

\-\--

影子状态X是如何得到的呢？下面先直接看完整代码吧。

public class KMP {

private int\[\]\[\] dp;

private String pat;

public KMP(String pat) {

this.pat = pat;

int M = pat.length();

// dp\[状态\]\[字符\] = 下个状态

dp = new int\[M\]\[256\];

// base case

dp\[0\]\[pat.charAt(0)\] = 1;

// 影子状态 X 初始为 0

int X = 0;

// 当前状态 j 从 1 开始

for (int j = 1; j \< M; j++) {

for (int c = 0; c \< 256; c++) {

if (pat.charAt(j) == c)

dp\[j\]\[c\] = j + 1;

else

dp\[j\]\[c\] = dp\[X\]\[c\];

}

// 更新影子状态

X = dp\[X\]\[pat.charAt(j)\];

}

}

public int search(String txt) {\...}

}

先解释一下这一行代码：

// base case

dp\[0\]\[pat.charAt(0)\] = 1;

这行代码是 base case，只有遇到 pat\[0\] 这个字符才能使状态从 0 转移到
1，遇到其它字符的话还是停留在状态 0（Java 默认初始化数组全为 0）。

影子状态X是先初始化为
0，然后随着j的前进而不断更新的。下面看看到底应该如何更新影子状态X：

int X = 0;

for (int j = 1; j \< M; j++) {

\...

// 更新影子状态

// 当前是状态 X，遇到字符 pat\[j\]，

// pat 应该转移到哪个状态？

X = dp\[X\]\[pat.charAt(j)\];

}

更新X其实和search函数中更新状态j的过程是非常相似的：

int j = 0;

for (int i = 0; i \< N; i++) {

// 当前是状态 j，遇到字符 txt\[i\]，

// pat 应该转移到哪个状态？

j = dp\[j\]\[txt.charAt(i)\];

\...

}

其中的原理非常微妙，注意代码中 for
循环的变量初始值，可以这样理解：后者是在txt中匹配pat，前者是在pat中匹配pat\[1:\]，状态X总是落后状态j一个状态，与j具有最长的相同前缀。所以我把X比喻为影子状态，似乎也有一点贴切。

另外，构建 dp 数组是根据 base casedp\[0\]\[..\]向后推演。这就是我认为
KMP 算法就是一种动态规划算法的原因。

至此，KMP 算法就已经再无奥妙可言了！看下 KMP 算法的完整代码吧：

public class KMP {

private int\[\]\[\] dp;

private String pat;

public KMP(String pat) {

this.pat = pat;

int M = pat.length();

// dp\[状态\]\[字符\] = 下个状态

dp = new int\[M\]\[256\];

// base case

dp\[0\]\[pat.charAt(0)\] = 1;

// 影子状态 X 初始为 0

int X = 0;

// 构建状态转移图（稍改的更紧凑了）

for (int j = 1; j \< M; j++) {

for (int c = 0; c \< 256; c++) {

dp\[j\]\[c\] = dp\[X\]\[c\];

dp\[j\]\[pat.charAt(j)\] = j + 1;

// 更新影子状态

X = dp\[X\]\[pat.charAt(j)\];

}

}

public int search(String txt) {

int M = pat.length();

int N = txt.length();

// pat 的初始态为 0

int j = 0;

for (int i = 0; i \< N; i++) {

// 计算 pat 的下一个状态

j = dp\[j\]\[txt.charAt(i)\];

// 到达终止态，返回结果

if (j == M) return i - M + 1;

}

// 没到达终止态，匹配失败

return -1;

}

}

经过之前的详细举例讲解，你应该可以理解这段代码的含义了，当然你也可以把
KMP 算法写成一个函数。核心代码也就是两个函数中 for
循环的部分，数一下有超过十行吗？

### **[labuladong]{.underline}**

你只要把住两点就行了：

1、遍历的过程中，所需的状态必须是已经计算出来的。

2、遍历的终点必须是存储结果的那个位置。

PS：但凡遇到需要递归的问题，最好都画出递归树，这对你分析算法的复杂度，寻找算法低效的原因都有巨大帮助

int fib(int n) {

if (n == 2 \|\| n == 1)

return 1;

int prev = 1, curr = 1;

for (int i = 3; i \<= n; i++) {

int sum = prev + curr;

prev = curr;

curr = sum;

}

return curr;

}

首先，这个问题是动态规划问题，因为它具有「最优子结构」的。要符合「最优子结构」，子问题间必须互相独立。啥叫相互独立？你肯定不想看数学证明，我用一个直观的例子来讲解。

比如说，你的原问题是考出最高的总成绩，那么你的子问题就是要把语文考到最高，数学考到最高......
为了每门课考到最高，你要把每门课相应的选择题分数拿到最高，填空题分数拿到最高......
当然，最终就是你每门课都是满分，这就是最高的总成绩。

得到了正确的结果：最高的总成绩就是总分。因为这个过程符合最优子结构，"每门科目考到最高"这些子问题是互相独立，互不干扰的。

但是，如果加一个条件：你的语文成绩和数学成绩会互相制约，此消彼长。这样的话，显然你能考到的最高总成绩就达不到总分了，按刚才那个思路就会得到错误的结果。因为子问题并不独立，语文数学成绩无法同时最优，所以最优子结构被破坏。

PS：为啥 dp 数组初始化为 amount + 1 呢，因为凑成 amount
金额的硬币数最多只可能等于 amount（全用 1 元面值的硬币），所以初始化为
amount + 1 就相当于初始化为正无穷，便于后续取最小值

最优子结构并不是动态规划独有的一种性质，能求最值的问题大部分都具有这个性质；但反过来，最优子结构性质作为动态规划问题的必要条件，一定是让你求最值的，以后碰到那种恶心人的最值题，思路往动态规划想就对了，这就是套路。

动态规划不就是从最简单的 base case
往后推导吗，可以想象成一个链式反应，以小博大。但只有符合最优子结构的问题，才有发生这种链式反应的性质

\-\-\-\-\-\-\-\-\--

「状态」很明显，就是当前拥有的鸡蛋数K和需要测试的楼层数N。随着测试的进行，鸡蛋个数可能减少，楼层的搜索范围会减小，这就是状态的变化。

「选择」其实就是去选择哪层楼扔鸡蛋。回顾刚才的线性扫描和二分思路，二分查找每次选择到楼层区间的中间去扔鸡蛋，而线性扫描选择一层层向上测试。不同的选择会造成状态的转移。

现在明确了「状态」和「选择」，动态规划的基本思路就形成了：肯定是个二维的dp数组或者带有两个状态参数的dp函数来表示状态转移；外加一个
for 循环来遍历所有选择，择最优的选择更新结果 ：

SuperEggDrop

Drop eggs is a very classical problem.

Some people may come up with idea O(KN\^2)

where dp\[K\]\[N\] = 1 + max(dp\[K - 1\]\[i - 1\],dp\[K\]\[N - i\]) for
i in 1\...N.

However this idea is very brute force, for the reason that you check all
possiblity.

So I consider this problem in a different way:

dp\[M\]\[K\]means that, given K eggs and M moves,

what is the maximum number of floor that we can check.

The dp equation is:

dp\[m\]\[k\] = dp\[m - 1\]\[k - 1\] + dp\[m - 1\]\[k\] + 1,

which means we take 1 move to a floor,

if egg breaks, then we can check dp\[m - 1\]\[k - 1\] floors.

if egg doesn\'t breaks, then we can check dp\[m - 1\]\[k\] floors.

dp\[m\]\[k\] is similar to the number of combinations and it increase
exponentially to N

public int superEggDrop(int K, int N) {

int\[\]\[\] floors = new int\[N + 1\]\[K + 1\];

int move = 0;

while (floors\[move\]\[K\] \< N) {

++m;

for (int egg = 1; egg \<= K; ++egg)

floors\[move\]\[egg\] = floors\[move - 1\]\[egg\] + 1 + floors\[move -
1\]\[egg - 1\];

}

return m;

}

The dp equation is:

dp\[m\]\[k\] = dp\[m - 1\]\[k - 1\] + dp\[m - 1\]\[k\] + 1,

assume, dp\[m-1\]\[k-1\] = n0, dp\[m-1\]\[k\] = n1

the first floor to check is n0+1.

if egg breaks, F must be in \[1,n0\] floors, we can use m-1 moves and
k-1 eggs to find out F is which one.

if egg doesn\'t breaks and F is in \[n0+2, n0+n1+1\] floors, we can use
m-1 moves and k eggs to find out F is which one.

So, with m moves and k eggs, we can find out F in n0+n1+1 floors,
whichever F is.

\-\--

Great, I understand this solution too.

The key concept of original O(KN\^2) solution is to try all the floor to
get the min cost min(max(broke, not broke)) as the answer.

This solution is somehow a reverse thinking:

1.  No matter which floor you try, egg will only break or not break, if
    > break, go to downstairs, if not break, go to upstairs.

2.  No matter you go up or go down, the num of all the floors is always
    > upstairs + downstairs + the floor you try, which is dp\[m\]\[k\] =
    > dp\[m - 1\]\[k - 1\] + dp\[m - 1\]\[k\] + 1.

====

the logic of \"dp\[m\]\[k\] = dp\[m - 1\]\[k - 1\] + dp\[m - 1\]\[k\] +
1\", my confusion is, if dp\[m - 1\]\[k - 1\] and dp\[m - 1\]\[k\] are
two different case break or not break; why we combine them together,
instead of use the smaller one? would you please explain more?

→

This one move will separate the floors into two non-overlapping groups,
below or above (the current level we choose to drop the egg); so no
matter what happened to the egg, we only need to check one of those two
group. If we need to check the level below the current level, then it
means the egg is break, so the maximum level we are able to check is
dp\[m - 1\]\[k - 1\]. Otherwise if we need to check the level above or
equal o the current level, it means the egg is not break, so the maximum
level we can check is dp\[m - 1\]\[k\], we should only return dp\[m -
1\]\[k - 1\] + dp\[m - 1\]\[k\]; however, we count the level from 0,
instead of 1, so we need to add the extra one level (i.e; if dp\[m -
1\]\[k - 1\] = 1 and dp\[m - 1\]\[k\] = 2, means we can check (2 + 3 ==
5) levels, so we need to return 4; which is dp\[m - 1\]\[k - 1\] + dp\[m
- 1\]\[k\] + 1)

Notes:

-   Find max "1" matrix in a square

Instead to create a cache and initialise all element by copying when I,j
=0.

Better solution is to clone input "matrix" this will lead to faster and
cleaner code

If(I=0 \|\| j=0) {// do nothing because those element remain unchanged
in matrix copy}

-   For Two sum, should raise Exception e.g. no findings rather than
    > return "null"

public int\[\] **[twoSum]{.underline}**(int\[\] nums, int target) {

for (int i = 0; i \< nums.length; i++) {

for (int j = i + 1; j \< nums.length; j++) { // I used int j=i, which is
wrong as it may cause one item to be used twice

if (nums\[j\] == target - nums\[i\]) {

return new int\[\] { i, j };

}

}

}

throw new IllegalArgumentException(\"No two sum solution\");

}

-   Return specific Exception, e.g.

throw new IllegalArgumentException(\"No two sum solution\");

-   Error of two sums

> if(map1.containsKey(diff)) {
>
> return new int\[\]{i, map1.get(diff)};
>
> } else{
>
> // be careful put number itself (rather than supplement) to map
>
> map1.put(nums\[i\], i);
>
> }

-   Summary:

    -   If possible, make use of HashMap to increase search performance

    -   If there are two loops, try to reduce to use one in-flight
        > hashmap lookup

-   Multiply string

    -   Naiive solution

> **ublic** String **[multiply]{.underline}**(String num1, String num2)
> {
>
> String n1 = **new** StringBuilder(num1).reverse().toString();
>
> String n2 = **new** StringBuilder(num2).reverse().toString();
>
> **int**\[\] d = **new** **int**\[num1.length()+num2.length()\];
>
> *//multiply each digit and sum at the corresponding positions*
>
> **for**(**int** i=0; i\<n1.length(); i++){
>
> **for**(**int** j=0; j\<n2.length(); j++){
>
> **d\[i+j\] += (n1.charAt(i)-\'0\') \* (n2.charAt(j)-\'0\');**
>
> }
>
> }
>
> StringBuilder sb = **new** StringBuilder();
>
> *//calculate each digit*
>
> **for**(**int** i=0; i\<d.length; i++){
>
> **int** mod = d\[i\]%10;
>
> **int** carry = d\[i\]/10;
>
> **if**(i+1\<d.length){
>
> d\[i+1\] += carry;
>
> }
>
> sb.insert(0, mod);
>
> }
>
> *//remove front 0\'s*
>
> **while**(sb.charAt(0) == \'0\' && sb.length()\> 1){
>
> sb.deleteCharAt(0);
>
> }
>
> **return** sb.toString();
>
> }
>
> \-\-\-\--Best Multiply String\-\--
>
> private static String multiply(String num1, String num2) {
>
> int nLen1 = num1.length(), nLen2=num2.length();
>
> int\[\] result = new int\[nLen1+nLen2\];
>
> for(int c1=nLen1-1;c1\>=0;c1\--) {
>
> for(int c2=nLen2-1;c2\>=0;c2\--){
>
> int nMulti= (num1.charAt(c1) - \'0\') \* (num2.charAt(c2) - \'0\');
>
> int sum = nMulti + result\[c1+c2+1\];
>
> result\[c1+c2\] += sum / 10; //This is for "carry", so must to be "+"
> in front of "="
>
> result\[c1+c2+1\] = sum % 10; // This is a reminder, so this only be
> assigned without "+"
>
> }
>
> }
>
> StringBuffer buff = new StringBuffer();
>
> for(int p:result) {
>
> if(!(result.length==0 && p==0)) {
>
> //remove prefix 0
>
> buff.append(p);
>
> }
>
> }
>
> return buff.toString();
>
> }

-   greedy algorithm

> \[Greedy\]
>
> const int N = 5;
>
> int Count\[N\] = {5,2,2,3,5};//每一张纸币的数量
>
> int Value\[N\] = {1,5,10,50,100};
>
> int **[solve]{.underline}**(int money) {
>
> int num = 0;
>
> for(int i = N-1;i\>=0;i\--) {
>
> int c = min(money/Value\[i\],Count\[i\]);//每一个所需要的张数
>
> money = money-c\*Value\[i\];
>
> num += c;//总张数
>
> }
>
> if(money\>0) num=-1;
>
> return num;
>
> }

-   Add One:

> private static int\[\] plusOneBest(int\[\] ary) {
>
> for (int i = ary.length - 1; i \>= 0; i\--) {
>
> if (ary\[i\] != 9) {
>
> ary\[i\]++; //\[!\] Here is key step, for two cases: (1) last digit,
> add one then exit (2) Next digit with carry, add on and exit
>
> break;
>
> } else {
>
> ary\[i\] = 0;
>
> }
>
> }
>
> if (ary\[0\] == 0) {
>
> int\[\] aryRtn = new int\[ary.length + 1\];
>
> System.arraycopy(aryRtn, 1, ary, 0, ary.length);
>
> aryRtn\[0\] = 1;
>
> return aryRtn;
>
> } else {
>
> return ary;
>
> }
>
> }

-   Add two Single nodes

> /\*\*
>
> \* Definition for singly-linked list.
>
> \* public class ListNode {
>
> \* int val;
>
> \* ListNode next;
>
> \* ListNode(int x) { val = x; }
>
> \* }
>
> \*/
>
> class Solution {
>
> public ListNode addTwoNumbers(ListNode l1, ListNode l2) {
>
> ListNode lResult = new ListNode(0);
>
> int carry=0,sum =0;
>
> ListNode itNode = lResult; // \[!\] to setup an iterator
>
> while(l1!=null \|\| l2!=null){
>
> // sum = l1.val + l2.val;
>
> sum = (l1!=null?l1.val:0) + (l2!=null?l2.val:0); // to void null in
> get reference
>
> sum += carry; // to accumulate \'carry\'
>
> carry = sum /10;
>
> // lResult.val = sum % 10;
>
> itNode.next = new ListNode(sum % 10);
>
> itNode = itNode.next; // \[!\] this is the key step
>
> if(l1!=null) {
>
> l1 = l1.next;
>
> }
>
> if(l2!=null){
>
> l2 = l2.next;
>
> }
>
> if(carry\>0) itNode.next = new ListNode(carry);
>
> }
>
> return lResult.next;
>
> }
>
> }

-   Longest unique characters

    -   Naive approach

> class Solution {
>
> public int lengthOfLongestSubstring(String s) {
>
> // analysis:
>
> // embeded two loops to foreach every element and inner loop step from
> current element of 1st loop
>
> // check whether each sub-string is all unique
>
> // if so, get length and compare with global temp max length
>
> int maxLen=0;
>
> for(int i=0;i\<s.length();i++) {
>
> //for inner loop, it start from i+1 (rather than i)
>
> for(int j=i+1;i\<=s.length();j++){
>
> if(noDup(s, i , j)){
>
> maxLen = Math.max(maxLen, (j-i));
>
> }
>
> }
>
> }
>
> return maxLen;
>
> }
>
> private boolean noDup(String sub, int start, int end){
>
> //check whether thsi sub string is unique
>
> // char\[\] aryOccurance=new char\[127\];
>
> // int\[\] aryOccurance=new int\[127\];
>
> Set\<Character\> set=new HashSet\<\>();
>
> for(int k=start;k\<end;k++){
>
> Character c = sub.charAt(k);
>
> if(set.contains(c)){
>
> return false;
>
> }else{
>
> set.add(c);
>
> }
>
> }
>
> return true;
>
> }
>
> }

-   Sliding window

> [[https://developpaper.com/share-several-algorithmic-interview-questions-related-to-sliding-window/]{.underline}](https://developpaper.com/share-several-algorithmic-interview-questions-related-to-sliding-window/)
>
> ***[Longest Substring Without Repeating Characters]{.underline}***
>
> public int lengthOfLongestSubstring(String s) {
>
> Map\<Character, Integer\> map= new HashMap\<\>();// map to cache
> position of each occruance
>
> int start=0, len=0;
>
> // abba
>
> for(int i=0; i\<s.length(); i++) {
>
> char c = s.charAt(i);
>
> if (map.containsKey(c)) {// here is the key step for "without
> repeating chars" in questions.
>
> if (map.get(c) \>= start)
>
> start = map.get(c) + 1;// found duplicate, so get started a new round,
> assign start from 1st occurance of 'duplicate char' plus one.
>
> }
>
> len = Math.max(len, i-start+1);
>
> map.put(c, i);
>
> }
>
> return len;
>
> }
>
> My solution vs leetcode one, latter one is much more consice
>
> // better solution leveraging slide window
>
> // Runtime: 12 ms, faster than 26.95% of Java online submissions for
> Longest Substring Without Repeating Characters.
>
> public int lengthOfLongestSubstring(String s){
>
> Set\<Character\> set =new HashSet\<\>();
>
> int maxLen = 0, left=0,right =-1, n=s.length();
>
> while(left\<n) {
>
> if((right+1)\<n && !set.contains(s.charAt(right+1))){
>
> // not in slide window
>
> right++;//expand slide window
>
> set.add(s.charAt(right));
>
> }else{
>
> // dup with existing slide window
>
> // shrink window
>
> set.remove(s.charAt(left));
>
> left++;
>
> }
>
> maxLen = Math.max(maxLen, right - left +1);// \[!\] be carefulf there
> is \"+1\" as this is for getting count
>
> }
>
> return maxLen;
>
> }
>
> \-\-\-\--leetcode solution\-\-\-\--
>
> public int lengthOfLongestSubstring(String s){
>
> int i=0,j=0,n=s.length(),rtn=0;
>
> Set\<Character\> set = new HashSet\<\>();
>
> while(i\<n && j\<n) {
>
> if(!set.contains(s.charAt(j))) {
>
> set.add(s.charAt(j++));
>
> rtn = Math.max(rtn, j-i) ;
>
> }else{
>
> set.remove(s.charAt(i++));
>
> }
>
> }
>
> return rtn;
>
> }
>
> \-\-\-\-\-\-\-\-\-\--

-   Palindrome integer (not string)

> class Solution {
>
> public boolean isPalindrome(int x) {
>
> //first of all, boundary (or edge case)
>
> if(x\<0 \|\| (x!=0 && x%10==0)) {
>
> return false;
>
> }
>
> int reverse =0;
>
> while(x\> reverse) {
>
> reverse = reverse \* 10 + x%10;
>
> x /= 10;
>
> }
>
> // When the length is an odd number, we can get rid of the middle
> digit by revertedNumber/10
>
> // For example when the input is 12321, at the end of the while loop
> we get x = 12, revertedNumber = 123,
>
> // since the middle digit doesn\'t matter in palindrome(it will always
> equal to itself), we can simply get rid of it.
>
> return x == reverse \|\| x == reverse/10;
>
> }
>
> }

-   Find longest common sub array among two arrays

\[DP\]

> public static int findLength\_dp(int\[\] A, int\[\] B) {
>
> // for dynamic programing, normally it compare itself with its
> sibling, using max/min
>
> // try to construct a matrix to keep track of path
>
> int m=A.length,n=B.length,max=0;
>
> int\[\]\[\] memo = new int\[m+1\]\[n+1\]; // \"+1\" to keep extra
> space
>
> for(int i = 0;i \<= m;i++) {
>
> for (int j = 0; j \<= n; j++) {
>
> //for DP, firstly to setup begin point
>
> if(i==0 \|\| j==0) {
>
> memo\[i\]\[j\]=0;
>
> }else{
>
> if(A\[i-1\]==B\[j-1\]){ // it they are same
>
> memo\[i\]\[j\] = 1+ memo\[i-1\]\[j-1\]; // increase one to cache
>
> max = Math.max(max,memo\[i\]\[j\]); // get global max
>
> }
>
> }
>
> }
>
> }
>
> return max;
>
> }

-   Dynamic programing:

重叠子问题、最优子结构、状态转移方程就是动态规划三要素。

What is dynamic programming?

Simply put, dynamic programming is an optimization technique that we can
use to solve problems where the same work is being repeated over and
over. You know how a web server may use caching? Dynamic programming is
basically that.

However, dynamic programming doesn't work for every problem. There are a
lot of cases in which dynamic programming simply won't help us improve
the runtime of a problem at all. If we aren't doing repeated work, then
no amount of caching will make any difference.

**A problem can be optimized using dynamic programming if it:**

1.  has an optimal substructure.

2.  has overlapping subproblems

**[Optimal substructure]{.underline}** simply means that you can find
the optimal solution to a problem by considering the optimal solution to
its subproblems.

### Overlapping Subproblems

[Overlapping
subproblems](https://en.wikipedia.org/wiki/Overlapping_subproblems) is
the second key property that our problem must have to allow us to
optimize using dynamic programming. Simply put, having overlapping
subproblems means we are computing the same problem more than once.

Imagine you have a server that caches images. If the same image gets
requested over and over again, you'll save a ton of time. However, if no
one ever requests the same image more than once, what was the benefit of
caching them?

**[Dynamic Programming Methods]{.underline}**
---------------------------------------------

DP offers two methods to solve a problem:

**1. Top-down with Memoization**

In this approach, we try to solve the bigger problem by recursively
finding the solution to smaller sub-problems. Whenever we solve a
sub-problem, we cache its result so that we don't end up solving it
repeatedly if it's called multiple times. Instead, we can just return
the saved result. This technique of storing the results of already
solved subproblems is called **Memoization**.

**2. Bottom-up with Tabulation**

Tabulation is the opposite of the top-down approach and avoids
recursion. In this approach, we solve the problem "bottom-up" (i.e. by
solving all the related sub-problems first). This is typically done by
filling up an n-dimensional table. Based on the results in the table,
the solution to the top/original problem is then computed.

Tabulation is the opposite of Memoization, as in Memoization we solve
the problem and maintain a map of already solved sub-problems. In other
words, in memoization, we do it top-down in the sense that we solve the
top problem first (which typically recurses down to solve the
sub-problems).

Let's apply Tabulation to our example of Fibonacci numbers. Since we
know that every Fibonacci number is the sum of the two preceding
numbers, we can use this fact to populate our table.

Here is the code for our bottom-up dynamic programming approach:

**class** Fibonacci {

**public** int CalculateFibonacci(int n) {

int dp\[\] = **new** int\[n+1\];

//base cases

dp\[0\] = 0;

dp\[1\] = 1;

**for**(int i=2; i\<=n; i++)

dp\[i\] = dp\[i-1\] + dp\[i-2\];

**return** dp\[n\];

}

**public** **static** void main(**String**\[\] args) {

Fibonacci fib = **new** Fibonacci();

**System**.out.println(\"5th Fibonacci is \-\--\> \" +
fib.CalculateFibonacci(5));

**System**.out.println(\"6th Fibonacci is \-\--\> \" +
fib.CalculateFibonacci(6));

**System**.out.println(\"7th Fibonacci is \-\--\> \" +
fib.CalculateFibonacci(7));

}

}

Generally speaking, dynamic programming is the technique of storing
repeated computations in memory, rather than recomputing them every time
you need them. The ultimate goal of this process is to improve runtime.
Dynamic programming allows you to use more space to take less time.

Dynamic programming relies on overlapping subproblems, because it uses
memory to save the values that have already been computed to avoid
computing them again. The more overlap there is, the more computational
time is saved.

**Top-down and bottom-up**

Top-down and bottom-up refer to two general approaches to dynamic
programming. A top-down solution starts with the final result and
recursively breaks it down into subproblems. The bottom-up method does
the opposite. It takes an iterative approach to solve the subproblems
first and then works up to the desired solution.

both solutions are equally valid and that one solution can be determined
from the other. In an interview situation, although bottom-up solutions
often result in more concise code, either approach is appropriate. I
recommend that you use whatever solution makes the most sense to you.

The important point is that top-down = recursive and bottom-up =
iterative.

> There are four steps in the FAST method:

1.  **F**irst solution

2.  **A**nalyze the first solution

3.  Identify the **S**ubproblems

4.  **T**urn the solution around

**First solution**

This is an important step for any interview question but is particularly
important for dynamic programming. This step finds the first possible
solution. This solution will be brute force and recursive. The goal is
to solve the problem without concern for efficiency. It means that if
you need to find the biggest/ smallest/longest/shortest something, you
should write code that goes through every possibility and then compares
them all to find the best one.

Your solution must also meet these restrictions:

-   The recursive calls must be self-contained. That means no global
    > variables.

-   You cannot do tail recursion. Your solution must compute the results
    > to each subproblem and then combine them afterwards.

-   Do not pass in unnecessary variables. Eg. If you can count the depth
    > of your recursion as you return, don't pass a count variable into
    > your recursive function.

> **Analyze the first solution**

In this step, we will analyze the first solution that you came up with.
This involves determining the time and space complexity of your first
solution and asking whether there is obvious room for improvement.

*// Compute the nth Fibonacci number recursively. // Optimized by
caching subproblem results* public int fib(int n) {

> if (n \< 2) return n;
>
> *// Create cache and initialize to -1*
>
> int\[\] cache = new int\[n+1\];
>
> for (int i = 0; i \< cache.length; i++) {
>
> cache\[i\] = -1;
>
> }
>
> *// Fill initial values in cache*
>
> cache\[0\] = 0;
>
> cache\[1\] = 1;
>
> return fib(n, cache);

}

*// Overloaded private method*

private int fib(int n, int\[\] cache) {

*// If value is set in cache, return*

> if (cache\[n\] \>= 0) return cache\[n\];
>
> *// Compute and add to cache before returning*
>
> cache\[n\] = fib(n-1, cache) + fib(n-2, cache);
>
> return cache\[n\];
>
> }

*Fig 3. Top-down dynamic Fibonacci solution*

> **Turn the solution around**

Since we now have a **top-down solution**, it is possible to reverse the
process and solve it from the bottom up. This ***[can be done by
starting with the base cases and building up the solution from there by
computing the results of each subsequent subproblem, until we reach our
result.]{.underline}***

In this problem, *[our base cases are fib(0) = 0 and fib(1) = 1. From
these two values, we can compute the next largest Fibonacci number,
fib(2) = fib(0) + fib(1). Once we have the value of fib(2), we can
calculate fib(3) etc. As we successively compute each Fibonacci number,
the previous values are saved and referred to as necessary, eventually
reaching fib(n).]{.underline}*

Our code for this process is fairly straightforward (*fig 5*).

This process yields a bottom-up solution. Since we iterate through all
of the numbers from 0 to n once, our time complexity will be O(n) and
our space will also be O(n), since we create a 1D array from 0 to n.
This makes our current solution comparable to the top-down solution,
although without recursion. This code is likely easier to understand.

*// Compute the nth Fibonacci number iteratively*

> public int fib(int n) {
>
> if (n == 0) return 0;
>
> *// Initialize cache*
>
> int\[\] cache = new int\[n+1\];
>
> cache\[1\] = 1;
>
> *// Fill cache iteratively*
>
> for (int i = 2; i \<= n; i++) {
>
> cache\[i\] = cache\[i-1\] + cache\[i-2\];
>
> }
>
> return cache\[n\];
>
> }
>
> *Fig 5. Bottom-up dynamic Fibonacci solution*
>
> it is possible to improve our solution further. During the computation
> process, we only refer to the most recent two subproblems
> (cache\[i-1\] and cache\[i-2\]) to compute the value of the current
> subproblem. Therefore, cache\[0\] through cache\[i-3\] are unnecessary
> and do not need to be kept in memory.

We can, therefore, improve the space complexity of our solution to O(1)
by only caching the most recent two values.

> *// Compute the nth Fibonacci number iteratively // with constant
> space. We only need to save // the two most recently computed values*
>
> public int fib(int n) {
>
> if (n \< 2) return n;
>
> int n1 = 1, n2 = 0;
>
> for (int i = 2; i \< n; i++) {
>
> int n0 = n1 + n2;
>
> n2 = n1;
>
> n1 = n0;
>
> }
>
> return n1 + n2;
>
> }

For any problem where you are asked **[to find the most/least/
largest/smallest]{.underline}** etc, an excellent technique **[is to
compare every possible combination]{.underline}**. Although it will be
inefficient, efficiency is not the most important current consideration
and a solution of that nature is easy to make dynamic.

> Make change
>
> // Brute force solution. Go through every
>
> // combination of coins that sum up to c to // find the minimum number
>
> public static int makeChange(int c) {
>
> int\[\] coins = new int\[\]{10, 6, 1};
>
> if (c == 0) return 0;
>
> int minCoins = Integer.*MAX\_VALUE*;
>
> // Try removing each coin from the total and // see how many more
> coins are required
>
> for (int coin : coins) {
>
> // Skip a coin if it's value is greater
>
> // than the amount remaining
>
> if (c - coin \>= 0) {
>
> int currMinCoins = *makeChange*(c - coin);
>
> if (currMinCoins \< minCoins)
>
> minCoins = currMinCoins;
>
> } }
>
> // Add back the coin removed recursively
>
> return minCoins + 1;
>
> }

-   How to convert one naive loop solution to dynamic programming
    > top-down approach

Based on this understanding, we can turn our solution into a top-down
dynamic solution. We can cache the results as they are computed. That
means that we will cache the minimum number of coins needed to make
various smaller amounts of change.

Like the Fibonacci problem, our code doesn't actually have to change
very much. It's only necessary to overload our function with another
that can initialize the cache. Then we update the original function in
order to check the cache before doing the computation and saving the
result to the cache afterwards

// Top down dynamic solution. Cache the values as we compute them

// transform naive approach to top-down need:

// overload existing method with new one accept cache

// while existing one do two tasks: (1) initialize cache (2) call new
method passing in cache

public int makeChange\_top\_down(int c) {

// Initialize cache with values as -1

int\[\] cache = new int\[c + 1\];

for (int i = 1; i \< c + 1; i++)

cache\[i\] = -1;

return makeChange\_top\_down(c, cache);

}

// Overloaded recursive function

private int makeChange\_top\_down(int c, int\[\] cache) {

int\[\] coins = new int\[\]{10, 6, 1};

// Return the value if it's in the cache

if (cache\[c\] \>= 0) return cache\[c\];

int minCoins = Integer.*MAX\_VALUE*; //declare result oppositely, e.g.
question is \"min\", so init return value would be Integer.MAX\_VALUE

// Find the best coin

for (int coin : coins) {

if (c - coin \>= 0) {

int currMinCoins =

makeChange\_top\_down(c - coin, cache);

if (currMinCoins \< minCoins)

minCoins = currMinCoins;

} }

// Save the value into the cache

cache\[c\] = minCoins + 1; // add one to the return value

return cache\[c\];

}

**Turn the solution around**

Once the top-down solution is completed, it's possible to flip it
around. We do this by solving the same subproblems in reverse order.
Rather than starting with our result in mind, we start with no change
and work our way up until we reach the solution.

The next step is to determine the subproblems that must be solved, in
order to solve successive subproblems. If we want to compute
makeChange(c), then we will have n different subproblems. If our coins
are {10, 6, 1}, we need to have the solutions for makeChange(c - 10),
makeChange(c - 6), and makeChange(c - 1).

Once makeChange() is solved for 0 through c - 1, it will be easy to
compute the value of makeChange(c). This is done by using the first
value, 0 as our base case. We can then compute the remaining values from
the previously computed values.

*// Bottom up dynamic programming solution. // Iteratively compute
number of coins for // larger and larger amounts of change*

public int makeChange(int c) {

int\[\] cache = new int\[c + 1\];

for (int i = 1; i \<= c; i++) {

int minCoins = Integer.MAX\_VALUE;

*// Try removing each coin from the total*

*// and see which requires the fewest*

*// extra coins*

for (int coin : coins) {

if (i - coin \>= 0) {

int currCoins = cache\[i-coin\] + 1;

if (currCoins \< minCoins) {

minCoins = currCoins;

}

} }

cache\[i\] = minCoins;

}

return cache\[c\];

}
