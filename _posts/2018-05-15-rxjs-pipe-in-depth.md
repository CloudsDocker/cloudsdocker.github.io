---
title: rxjs pipe in depth
tags:
- RxJS
- NodeJs
- Angular
layout: posts
---
https://stormforger.com/blog/2016/07/08/types-of-performance-testing/

Learn more about load testing, scalability testing, stress, spike and soak testing, configuration testing as well as availability and resilience testing. 


-----------15/05/2018 notes ---------------
https://blog.hackages.io/rxjs-5-5-piping-all-the-things-9d469d1b3f44
RxJS 5.5, piping all the things

So now we want a way to use those operators, how could we do that?

Well, we said those operators are “lettable” that means we can use them by calling the let method on an observable:

And if we want to chain multiple lettable operators we can keep dot chaining:

import { Observable } from 'rxjs/Rx';
import { filter, map, reduce } from 'rxjs/operators';

const filterOutEvens = filter(x => x % 2);
const sum = reduce((acc, next) => acc + next, 0);
const doubleBy = x => map(value => value * x);

const source$ = Observable.range(0, 10);

source$
  .let(filterOutEvens)
  .let(doubleBy(2))
  .let(sum)
  .subscribe(x => console.log(x)); // 50

  ---
  Meaning we can easily compose a bunch of pure function operators and pass them as a single operator to an observable!

Conclusion
With those tools in hand, you can write RxJS code that is much more re-usable by just piping your (pure functions) operators together and easily re-use shared logic.


  import { Observable, pipe } from 'rxjs/Rx';
import { filter, map, reduce } from 'rxjs/operators';

const filterOutEvens = filter(x => x % 2);
const sum = reduce((acc, next) => acc + next, 0);
const doubleBy = x => map(value => value * x);

const complicatedLogic = pipe(
  filterOutEvens,
  doubleBy(2),
  sum
);

const source$ = Observable.range(0, 10);

source$.let(complicatedLogic).subscribe(x => console.log(x)); // 50


https://github.com/ReactiveX/rxjs/blob/master/doc/pipeable-operators.md
What?
What is a pipeable operator? Simply put, a function that can be used with the current let operator. It used to be the origin of the name ("lettable"), but that was confusing and we call them "pipeable" now because they're intended to be used with the pipe utility. `A pipeable operator is basically any function that returns a function with the signature: <T, R>(source: Observable<T>) => Observable<R>.`

There is a pipe method built into Observable now at Observable.prototype.pipe that сan be used to compose the operators in similar manner to what you're used to with dot-chaining (shown below).

There is also a pipe utility function at rxjs/util/pipe that can be used to build reusable pipeable operators from other pipeable operators.

## Usage
You pull in any operator you need from one spot, under 'rxjs/operators' (plural!). It's also recommended to pull in the Observable creation methods you need directly as shown below with range:

```typescript
import { range } from 'rxjs/observable/range';
import { map, filter, scan } from 'rxjs/operators';

const source$ = range(0, 10);

source$.pipe(
  filter(x => x % 2 === 0),
  map(x => x + x),
  scan((acc, x) => acc + x, 0)
)
.subscribe(x => console.log(x))
```


https://blog.angularindepth.com/rxjs-understanding-lettable-operators-fe74dda186d3
RxJS: Understanding Lettable Operators

## What are lettable operators and what does lettable mean?
If lettable operators are used with a method named pipe, you might wonder why they are referred to as lettable. The term is derived from RxJS’s let operator.

`The let operator is conceptually similar to the map operator, but instead of taking a projection function that receives and returns a value, let takes a function that receives and returns an observable. ` It’s unfortunate that let is one of the less-well-known operators, as it’s very useful for composing reusable functionality.


```typescript
import * as Rx from "rxjs";

export function retry<T>(
  count: number,
  wait: number
): (source: Rx.Observable<T>) => Rx.Observable<T> {

  return (source: Rx.Observable<T>) => source
    .retryWhen(errors => errors
      // Each time an error occurs, increment the accumulator.
      // When the maximum number of retries have been attempted, throw the error.
      .scan((acc, error) => {
        if (acc >= count) { throw error; }
        return acc + 1;
      }, 0)
      // Wait the specified number of milliseconds between retries.
      .delay(wait)
    );
}
```
When retry is called, it’s passed the number of retry attempts that should be made and the number of milliseconds to wait between attempts, and it returns a function that receives an observable and returns another observable into which the retry logic is composed. The returned function can be passed to the let operator, like this:

```typescript
import * as Rx from "rxjs";
import { retry } from "./retry";

const name = Rx.Observable.ajax
  .getJSON<{ name: string }>("/api/employees/alice")
  .let(retry(3, 1000))
  .map(employee => employee.name)
  .catch(error => Rx.Observable.of(null));
 ``` 

Using the let operator, we’ve been able to create a reusable function much more simply than we would have been able to create a prototype-patching operator. What we’ve created is a lettable operator.

Lettable operators are a higher-order functions. Lettable operators return functions that receive and return observables; and those functions can be passed to the let operator.

We can also use our lettable retry operator with pipe, like this:
```typescript
import { ajax } from "rxjs/observable/dom/ajax";
import { of } from "rxjs/observable/of";
import { catchError, map } from "rxjs/operators";
import { retry } from "./retry";

const name = ajax
  .getJSON<{ name: string }>("/api/employees/alice")
  .pipe(
    retry(3, 1000),
    map(employee => employee.name),
    catchError(error => of(null))
  );
```


Let’s return to our retry function and replace the chained methods with lettable operators and a pipe call, so that it looks like this:
```typescript
import { Observable } from "rxjs/Observable";
import { delay, retryWhen, scan } from "rxjs/operators";

export function retry<T>(
  count: number,
  wait: number
): (source: Observable<T>) => Observable<T> {

  return retryWhen(errors => errors.pipe(
    // Each time an error occurs, increment the accumulator.
    // When the maximum number of retries have been attempted, throw the error.
    scan((acc, error) => {
      if (acc >= count) { throw error; }
      return acc + 1;
    }, 0),
    // Wait the specified number of milliseconds between retries.
    delay(wait)
  ));
}
```
With the chained methods replaced, we now have a proper, reusable lettable operator that imports only what it requires.

## Why should lettable operators should be preferred?
For application developers, lettable operators are much easier to manage:

* Rather then relying upon operators being patched into Observable.prototype, lettable operators are explicitly imported into the modules in which they are used.
* It’s easy for TypeScript and bundlers to determine whether the lettable operators imported into a module are actually used. And if they are not, they can be left unbundled. If prototype patching is used, this task is manual and tedious.
* For library authors, lettable operators are much less verbose than call-based alternative, but it’s the correct inference of types that is — at least for me — the biggest advantage.

---
Agreed, the pipe is awesome for composing custom rx operators. But why do we see more and more people using it even when not combining re-usable variables — instead of just chaining methods?

Meaning, we use to write e.g…

const source$ = Observable.range(0, 10); 
source$
  .filter(x => x % 2)
  .reduce((acc, next) => acc + next, 0)
  .map(value => value * 2)
  .subscribe(x => console.log(x));
Above is imho much cleaner than what I see more nowadays:

const source$ = Observable.range(0, 10);
source$.pipe(
  filter(x => x % 2),
  reduce((acc, next) => acc + next, 0),
  map(value => value * 2)
).subscribe(x => console.log(x));
Are there performance advantages by using the standalone operators instead of chaining?

------------
https://webpack.js.org/guides/tree-shaking/
Tree shaking is a term commonly used in the JavaScript context for dead-code elimination. It relies on the static structure of ES2015 module syntax, i.e. import and export. The name and concept have been popularized by the ES2015 module bundler rollup.


So, what we've learned is that in order to take advantage of tree shaking, you must...

Use ES2015 module syntax (i.e. import and export).
Add a "sideEffects" entry to your project's package.json file.
Include a minifier that supports dead code removal (e.g. the UglifyJSPlugin).



--- english---
it can safely prune unused exports.

Trim (a tree, shrub, or bush) by cutting away dead or overgrown branches or stems, especially to encourage growth.

‘now is the time to prune roses’
