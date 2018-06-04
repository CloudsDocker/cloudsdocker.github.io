---
Layout: page
title: JavaScript tips
tag:
- Coding
- JavaScript
---

# includes() vs some()

* The includes() method is used to check if a specific string exists in a collection, and returns true or false. Keep in mind that it is case sensitive: if the item inside the collection is SCHOOL, and you search for school, it will return false.

* The some() method checks if some elements exists in an array, and returns true or false. This is somewhat similar to the concept of the includes() method, `the key diffence is the argument is a function` but not a string.

# Observable is `lazy`

Remember that observables are lazy — if we want to pull a value out of an observable, we must subscribe().

# mergeAll vs mergeMap in redux

## mergeAll

When the inner observable emits, let me know by merging the value to the outer observable.

Under the hood, the mergeAll() operator basically does takes the inner observable, subscribes to it, and pushes the value to the observer. Here is one sample:


```typescript
const click$ = Observable.fromEvent(button, ‘click’);
const interval$ = Observable.interval(1000);

const observable$ = click$.map(event => { 
   return interval$;
});

observable$.mergeAll().subscribe(num => console.log(num));

Because this is a common pattern in Rx, there is a shortcut that achieves the same behaviour — mergeMap().


const click$ = Observable.fromEvent(button, ‘click’);
const interval$ = Observable.interval(1000);

const observable$ = click$.mergeMap(event => { 
   return interval$;
});

observable$.subscribe(num => console.log(num));
```

#  more elegant, concise and flexible approach to check host string belongs to multiple value choices
checkStringAgainstMultipleLiteralValues.js
```javascript
if (host.match(/["uat" , "beta", "lab"].(api.)?yourdomain.(com.)?["au","io"]/)) {
    console.log('matched')
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
