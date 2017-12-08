---
Layout: page
title: JavaScript tips
tag:
- Coding
- JavaScript
---

#  more elegant, concise and flexible approach to check host string belongs to multiple value choices
checkStringAgainstMultipleLiteralValues.js
```javascript
if (host.match(/["uat" , "beta", "lab"].(api.)?youdomain.(com.)?["au","io"]/)) {
    // if (host.match('/[beta|uat|lab]/i')) {
    console.log('matched1111')
}
```
# closure 

闭包就是一个函数引用另外一个函数的变量，因为变量被引用着所以不会被回收，因此可以用来封装一个私有变量。这是优点也是缺点，不必要的闭包只会徒增内存消耗！另外使用闭包也要注意变量的值是否符合你的要求，因为他就像一个静态私有变量一样。

 In JavaScript, if you use the function keyword inside another function, you are creating a closure.
 
 Two one sentence summaries about closure

- closure is the local variable for a function — kept alive after the function has returned, or
- closure is a stack-frame which is not deallocated when the function returns (as if a 'stack-frame' were malloc'ed instead of being on the stack!).
 
 In JavaScript, if you declare a function within another function, then the local variables can remain accessible after returning from the function you called. 
 

# Tips to redirect page

It's better to use `window.location.replace("httpxxx")', rather than window.location.href="xxx". Because `replace` will not save the page in the session history, so users won't get stufy in never-ending back-button fiasco.
