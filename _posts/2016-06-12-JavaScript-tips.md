---
Layout: page
title: JavaScript tips
tags:
 - Coding
 - JavaScript
layout: posts
---

# includes() vs some()

* The includes() method is used to check if a specific string exists in a collection, and returns true or false. Keep in mind that it is case sensitive: if the item inside the collection is SCHOOL, and you search for school, it will return false.

* The some() method checks if some elements exists in an array, and returns true or false. This is somewhat similar to the concept of the includes() method, `the key diffence is the argument is a function` but not a string.

# splice vs slice

splice: Join or connect (a rope or ropes) by interweaving the strands at the ends.

‘we learned how to weave and splice ropes’

slice: Cut (something, especially food) into slices.

‘slice the onion into rings’



1. The splice() method returns the removed item(s) in an array and slice() method returns the selected element(s) in an array, as a new array object.

2. The splice() method changes the original array and slice() method doesn’t change the original array.

3. The splice() method can take n number of arguments:

Argument 1: Index, Required. An integer that specifies at what position to add /remove items, Use negative values to specify the position from the end of the array.

Argument 2: Optional. The number of items to be removed. If set to 0(zero), no items will be removed. And if not passed, all item(s) from provided index will be removed.

Argument 3…n: Optional. The new item(s) to be added to the array.


           -5 -4 -3 -2 -1
            |  |  |  |  |
var array4=[16,17,18,19,20];
             |  |  |  |  |
             0  1  2  3  4
 
```javascript
 console.log(array4.splice(-2,1,"me"));
// shows  [19]
 
console.log(array4);
// shows [16, 17, 18, "me", 20]
```

The slice() method can take 2 arguments:

Argument 1: Required. An integer that specifies where to start the selection (The first element has an index of 0). Use negative numbers to select from the end of an array.

Argument 2: Optional. An integer that specifies where to end the selection. If omitted, all elements from the start position and to the end of the array will be selected. Use negative numbers to select from the end of an array.

```javascript
var array=[1,2,3,4,5]
console.log(array.slice(2));
// shows [3, 4, 5], returned selected element(s).
```


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
