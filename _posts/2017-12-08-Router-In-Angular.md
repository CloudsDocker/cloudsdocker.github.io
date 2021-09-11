---
title: RxJS reactive extension javascript
tags:
- Angular
- JavaScript
- NodeJs
layout: posts
---

# Streams

Traditionally, the term stream was used in programming languages as an abstract object related to I/O operations such as reading a file, reading a socket, or requesting data from an HTTP server. For instance, Node.js implements readable, writable, and duplex streams for doing just this. In the RP world, we expand the definition of a stream to mean any data source that can be consumed.
```javascript
A$ = [20];                                        1
B$ = [22];                                        2
C$ = A$.concat(B$).reduce(adder); //-> [42]       3

A$.push(100);                                     4
C$ = ?
```

1 Creates a stream initialized with the value 20
2 Creates a stream initialized with the value 22
3 Concatenates both streams and applies an adder function to get a new container with 42
4 Pushes a new value into A$
First, we’ll explain some of the notation we use here. Streams are containers or wrappers of data very similar to arrays, so we used the array literal notation [] to symbolize this. Also, it’s common to use the $ suffix to qualify variables that point to streams. In the RxJS community, this is known as Finnish Notation, attributed to Andre Staltz, who is one of the main contributors of RxJS and Finnish.

# Array extras

JavaScript ES5 introduced new array methods, known as the array extras, which enable some level of native support for FP. These include map, reduce, filter, some, every, and others
Reactive programming is oriented around data flows and propagation. In this case, you can think of C$ as an always-on variable that reacts to any change and causes actions to ripple through it when any constituent part changes. Now let’s see how RxJS implements this concept.


If you were to visit the main website for the Reactive Extensions project (http://reactivex.io/), you’d find it defined as “an API for asynchronous programming with observable streams.” 

Definition

A stream is nothing more than a sequence of events over time.
Everything is a stream
The concept of a stream can be applied to any data point that holds a value; this ranges from a single integer to bytes of data received from a remote HTTP call. RxJS provides lightweight data types to subscribe to and manage streams as a whole that can be passed around as first-class objects and combined with other streams. 
RxJS provides lightweight data types to subscribe to and manage streams as a whole that can be passed around as first-class objects and combined with other streams. Learning how to manipulate and use streams is one of the central topics of this book. At this point, we haven’t talked about any specific RxJS objects; for now, we’ll assume that an abstract data type, a container called Stream, exists. You can create one from a single value as such:

Stream(42);
At this point, this stream remains dormant and nothing has actually happened, until there’s a subscriber (or observer) that listens for it. This is very different from Promises, which execute their operations as soon as they’re created. Instead, streams are lazy data types, which means that they execute only after a subscriber is attached. In this case, the value 42, which was lifted into the stream context, navigates or propagates out to at least one subscriber. After it receives the value, the stream is completed:


```javascript
Stream(42).subscribe(
   val => {                                             1
      console.log(val); //-> prints 42
   }
);
```


This creates two important challenges: scalability and latency.

As more and more data is received, the amount of memory that your application consumes or requires will grow linearly or, in worst cases, exponentially; this is the classic problem of scalability, and trying to process it all at once will certainly cause the user interface (UI) to become unresponsive. Buttons may no longer appear to work, fancy animations will lag, and the browser may even flag the page to terminate, which is an unacceptable notion for modern web users.

This problem is not new, though in recent years there has been exponential growth in the sheer scale of the number of events and data that JavaScript applications are required to process. This quantity of data is too big to be held readily available and stored in memory for use. Instead, we must create ways to fetch it from remote locations asynchronously, resulting in another big challenge of interconnected software systems: latency, which can be difficult to express in code.
you’ll first learn about the fundamental principles of two emerging paradigms: functional programming (FP) and reactive programming (RP). This exhilarating composition is what gives rise to functional reactive programming (FRP), encoded in a library called RxJS (or rx.js), which is the best prescription to deal with asynchronous and event-based data sources effectively.
By subscribing to a stream, your code expresses an interest in receiving the stream’s elements. During subscription, you specify the code to be invoked when the next element is emitted, and optionally the code for error processing and stream completion. Often you’ll specify a number of chained operators and then invoke the subscribe() method

The subscribe() method creates the instance of Observer, which in this case passes each value from the stream generated by the searchInput to the getStockQuoteFromServer() method. In a real-world scenario, this method would issue a request to the server,
No matter how many operators you chain together, none of them will be invoked on the stream until you invoke subscribe().
If you prefer to generate an observable stream based on another event (such as on keyup), you can use the RxJS Observable.fromEvent() API (see the RxJS 
One of the benefits of observables over promises is that the former can be canceled. 
Observable1 → switchMap(function) → Observable2 → subscribe()

You’re switching over from the first observable to the second one. If Observable1 pushes the new value but the function that creates Observable2 hasn’t finished yet, it’s killed; switchMap() unsubscribes and resubscribes to Observable1 and starts handling the new value from this stream.

If the observable stream from the UI pushes the next value before getWeather() has returned its observable value, switchMap() kills the running getWeather(), gets the new value for the city from the UI, and invokes getWeather() again. While killing getWeather(), it also aborts the HTTP request that was slow and didn’t complete in time.

The first argument of subscribe() contains a callback for handling data coming from the server. The code in this arrow expression is specific to the API provided by the weather service. You just extract the temperature and humidity from the returned JSON. The API offered by this particular weather service stores the error codes in the response, so you manually handle the status 404 here and not in the error-handler callback.

Now let’s verify that canceling previous requests works. Typing the word London takes more than the 200 milliseconds specified in debounceTime(), which means the valueChanges event will emit the observable data more than once. To ensure that the request to the server takes more than 200 milliseconds, you need a slow internet connection.

Note

Listing 5.5 has lots of code in the constructor, which may look like a red flag to developers who prefer using constructors only to initialize variables and not to execute any code that takes time to complete. If you take a closer look, though, you’ll notice that it just creates a subscription to two observable streams (UI events and HTTP service). No actual processing is done until the user starts entering the name of a city, which happens after the component is already rendered.

We ran the preceding example and then turned on throttling in Chrome Developer Tools, emulating a slow GPRS connection. Typing the word London resulted in four getWeather() invocations: for Lo, Lon, Lond, and London. Accordingly, four HTTP requests were sent over the slow connection, and three of them were automatically canceled by the switchMap() operator, as shown in figure 5.10.

Figure 5.10. Running observable_events_http.ts



With very little programming, you saved bandwidth by eliminating the need for the server to send four HTTP responses for cities you’re not interested in and that may not even exist. As we stated in chapter 1, a good framework is one that allows you to write less code.
Angular comes with a number of predefined pipes, and each pipe has a class that implements its functionality (such as DatePipe) as well as the name you can use in the template (such as date):

UpperCasePipe allows you to convert an input string into uppercase by using | uppercase in the template.
DatePipe lets you display a date in different formats by using | date.
CurrencyPipe transforms a number into a desired currency by using | currency.
AsyncPipe will unwrap the data from the provided observable stream by using | async. You’ll see a code sample that uses async in chapter 8.
Some pipes don’t require input parameters (such as uppercase), and some do (such as date:'medium'). You can chain as many pipes as you want. The next code snippet shows how to display the value of the birthday variable in a medium date format and in uppercase (for example, JUN 15, 2001, 9:43:11 PM):

Custom pipes
In addition to predefined pipes, Angular offers a simple way to create custom pipes, which can include code specific to your application. You need to create a @Pipe annotated class that implements the PipeTransform interface. The PipeTransform interface has the following signature:

export interface PipeTransform {
  transform(value: any, ...args: any[]): any;
}
This tells you that a custom pipe class must implement just one method with the preceding signature. The first parameter of transform takes a value to be transformed, and the second defines zero or more parameters required for your transformation algorithm. The @Pipe annotation is where you specify the name of the pipe to be used in the template. If your component uses custom pipes, they have to be explicitly listed in its @Component annotation in the pipes property.

In the previous section, the weather example displayed the temperature in London in Fahrenheit. But most countries use the metric system and show temperature in Celsius. Let’s create a custom pipe that can convert the temperature from Fahrenheit to Celsius and back. The code of the custom TemperaturePipe pipe (see the following listing) can be used in a template as temperature.

Listing 5.6. temperature-pipe.ts



Next comes the code of the component (pipe-tester.ts) that uses the temperature pipe. Initially this program will convert the temperature from Fahrenheit to Celsius (the FtoC format). By clicking the toggle button, you can change the direction of the temperature conversion
Event emitters
Event emitters are popular mechanisms for asynchronous event-based architectures. The DOM, for instance, is probably one of the most widely known event emitters. On a server like Node.js, certain kinds of objects periodically produce events that cause functions to be called. In Node.js, the EventEmitter class is used to implement APIs for things like WebSocket I/O or file reading/writing so that if you’re iterating through directories and you find a file of interest, an object can emit an event referencing this file for you to execute any additional code.
ajax('<host1>/items',
   items => {
       for (let item of items) {
          ajax(`<host2>/items/${item.getId()}/info`,
          dataInfo => {
          ajax(`<host3>/files/${dataInfo.files}`,
          processFiles);
       });
    }
});
—is known to be continuation-passing style (CPS), because none of the functions are explicitly waiting for a return value. But as we mentioned, abusing this makes code hard to reason about. What you can do is to make continuations first-class citizens and actually define a concrete interpretation of what it means to “continue.” So, we introduce the notion of then: “Do X, then do Y,” to create code that reads like this:

Fetch all items, then                                          1
   For-each item fetch all files, then                         1
      Process each file
1 The key term “then” suggests time and sequence.
This is where Promises come in. A Promise is a data type that wraps an asynchronous or long-running operation, a future value, with the ability for you to subscribe to its result or its error. A Promise is considered to be fulfilled when its underlying operation completes, at which point subscribers will receive the computed result.

Because we can’t alter the value of a Promise once it’s been executed, it’s actually an immutable type, which is a functional quality we seek in our programs. 
ajax('<host1>/items')
  .then(items =>
    items.forEach(item =>
      ajax(`<host2>/data/${item.getId()}/info`)
       .then(dataInfo =>
         ajax(`<host3>/data/files/${dataInfo.files}`)
       )
       .then(processFiles);
    )
  );
This looks similar to the previous statement! Being a more recent addition to the language with ES6 and inspired in FP design, Promises are more versatile and idiomatic than callbacks. Applying these functions declaratively—meaning your code expresses the what and not the how of what you’re trying to accomplish—into then blocks allows you to express side effects in a pure manner.

let getItems = () => ajax('<host1>/items');
let getInfo  = item => ajax(`<host2>/data/${item.getId()}/info`);
let getFiles = dataInfo => ajax(`<host3>/data/files/${dataInfo.files}`);
and then use Promises to stitch together our asynchronous flow. We use the Promise.all() function to map an array of separate Promises into a single one containing an array of results:

getItems()
  .then(items => items.map(getInfo))
  .then(promises => Promise.all(promises))
  .then(infos => infos.map(getFiles))
  .then(promises => Promise.all(promises))
  .then(processFiles);
The use of then() explicitly implies that there’s time involved among these calls, which is a really good thing. If any step fails, we can also have matching catch() blocks to handle errors and potentially continue the chain of command if necessary, a

Figure 1.7. Promises create a flow of calls chained by then methods. If the Promise is fulfilled, the chain of functions continues; otherwise, the error is delegated to the Promise catch block.


The drawback of using Promises is that they’re unable to handle data sources that produce more than one value, like mouse movements or sequences of bytes in a file stream. Also, they lack the ability to retry from failure—all present in RxJS. 
The most important downside, moreover, is that because Promises are immutable, they can’t be cancelled. So, for instance, if you use a Promise to wrap the value of a remote HTTP call, there’s no hook or mechanism for you to cancel that work. This is unfortunate because HTTP calls, based on the XmlHttpRequest object, can be aborted,[3] but this feature isn’t honored through the Promise interface. 

It’s difficult to detect when events or long-running operations go rogue and need to be cancelled. Consider the case of a remote HTTP request that’s taking too long to process. Is the script unresponsive or is the server just slow? It would be ideal to have an easy mechanism to cancel events cleanly after some predetermined amount of time. Implementing your own cancellation mechanism can be very challenging and error prone even with the help of third-party libraries.

One good quality of responsive design is to always throttle a user’s interaction with any UI components, so that the system isn’t unnecessarily overloaded. In chapter 4, you’ll learn how to use throttling and debouncing to your advantage. Manual solutions for achieving this are typically very hard to get right and involve functions that access data outside their local scope, which breaks the stability of your entire program
You learned that Promises certainly move the needle in the right direction (and RxJS integrates with Promises seamlessly if you feel the need to do so). 

But what you really need is a solution that abstracts out the notion of latency away from your code while allowing you to model your solutions using a linear sequence of steps through which data can flow over time


THE REACTIVE EXTENSIONS FOR JAVASCRIPT
Reactive Extensions for JavaScript (RxJS) is an elegant replacement for callback or Promise-based libraries, using a single programming model that treats any ubiquitous source of events—whether it be reading a file, making an HTTP call, clicking a button, or moving the mouse—in the exact same manner. For example, instead of handling each mouse event independently with a callback, with RxJS you handle all of them combined.



```javascript

```



# Reference
- https://angular.io/guide/router
