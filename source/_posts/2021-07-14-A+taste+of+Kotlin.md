---
title: A Taste of Kotlin
tags:
- Kotlin
- Java
---


# Execution summary
Kotlin gives you `compile-time null-safety` and `less boilerplate`. Kotlin and Java is NOT mutex, you can (and I know many company do) keep your project contains both Java and Kotlin source.

Kotlin is interchangeable with Java irrespective of difference between Java vs Kotlin. We can call Kotlin code in Java and Java code in Kotlin. So we can have both Java vs Kotlin classes side by side in a project and compiles without any issues. After compilation we unable to find which class written in Java or Kotlin.

> In a nutshell, Kotlin would helpful to bring in concise robust and more readable code. It will eliminate many boiler plate code in Java, as normally less code means less bug , less support tasks and easier for code review



## Why to chose Kotlin
 Lot's company are using Kotlin in their production, which prove it's a mature product to use
Google
Amazon
Netflix
JetBrains (obviously)
Goldman Sachs
Credit Suisse
J.P. Morgan

### Migration is simple and almost effort-less
 Automate and easy
Convert from Java to Kotlin can be started in very easy and auto way. For example, in IntelliJ IDE, if you copy Java code to one Kotlin file (*.kt), it will prompt up one window to suggest you do such conversation for you. As below screenshot:

Automatic convert by out-of-box IntellijJ tool



#### Transparent to Production runtime and Ops
Kotlin is one JVM language, it will compile to byte code which is same as Java. So from runtime environment, there is no different for code coded in Java or Kotlin.



## Key Features would be useful to us. 
> In other words, what Kotlin can bring to us, to improve code quality in your projects

   - . Null pointer check
To handle million dollar worth errors (NPE) elegantly and safely. Quickly checkout following summary 

```java
/*
 Get rid of those pesky NullPointerExceptions, you know, The Billion Dollar Mistake
*/

var output: String
output = null   // Compilation error

// Kotlin protects you from mistakenly operating on nullable types

val name: String? = null    // Nullable type
println(name.length())      // Compilation error
```

Here are some more examples

***First sample***


```java
protected synchronized BigDecimal getThePrice(Info product) throws Exception {
		...
		String benchmark = product.getBenchMark();

		if(benchmark != null) {
			Info fProduct = getProduct(benchmark);

			if(fProduct != null) {
				BigDecimal closePrice = new BigDecimal(fProduct.getLast()).divide(TEN_THOUSAND);

				if(closePrice != null ) {
					return closePrice.subtract(openPrice);
				}
			}
...
```

Those incremental nested Null checking is not only lengthy and boiler plate tend to error prone  `Null checking` can be eliminated by Kotlin outstanding Null pointer checking feature. As below sample code


```java
@Synchronized
@Throws(Exception::class)
protected fun getPrice(product: Info): BigDecimal? {
   ...
   return product.getBenchMark()?.let { getProduct(it) }?.let { BigDecimal(it.getLastBP()).divide(TEN_THOUSAND) }?.subtract(closePrice)
```

*** 2nd example***
Replace following code
```java

        if(modifier != null)
        	modifier.modifyFields(fields);

        // Here the dealer is feeding prices in to the price feed, as his/her prices
        if(priceFeed != null) {
        	String result = priceFeed.sendIndicative(dealer.getUserId(), "autoquote", fields);
        	if(result != null)
        		LOG.info("Some error in send indicative: " + result);
        } else {
        	LOG.info("Price feed was not started");
        }
```

To


```java
modifier?.modifyFields(fields)
// Here the dealer is feeding prices in to the price feed, as his/her prices
priceSender?.sendPrice(dealer.getUserId(), "quote", fields)?.let { LOG.info("Some error in send price: $it") }
   ?: LOG.info("Price feed was not started")
```

  - .  Data class

For some class files which is purely serve as Data Object a.k.a POJO, Java requires to declare each member properties separately , create getter and setter for each property. Almost majority of the code are boilterplate, rather than business logic . So this can be solved in Kotlin by one line. Here is one sample class
```java
public class AllocationRuleDto {

	private Integer id;
	private Integer userId;
	private Integer productTypeId;
	private Integer counterpartyId;
	private Integer accountId;
	private Integer clearingHouseId;

	public AllocationRuleDto(Integer id, Integer userId, Integer productTypeId, Integer counterpartyId, Integer accountId, Integer clearingHouseId) {
		this.id = id;
		this.userId = userId;
		this.productTypeId = productTypeId;
		this.counterpartyId = counterpartyId;
		this.accountId = accountId;
		this.clearingHouseId = clearingHouseId;
	}

	public Integer getId() {
		return id;
	}

	public Integer getUserId() {
		return userId;
	}

	public Integer getProductTypeGroupId() {
		return productTypeId;
	}

	public Integer getCounterpartyId() {
		return counterpartyId;
	}

	public Integer getAccountId() {
		return accountId;
	}

	public Integer getClearingHouseId() {
		return clearingHouseId;
	}
```

Here is the Kotlin version to serve same purpose, it will implement similar constructor, getter, setter features automatically.

```java
data class AllocationRuleDto(val id: Int, val userId: Int, val productTypeId: Int, val counterpartyId: Int, val accountId: Int, val clearingHouseId: Int)
```

   - .Functional programming and Kotlin built-in functionalities Type inference

```java
var a = "10"
String template
val message = "$n is ${if(n > 0) "positive" else "not positive"}
```

   - Secondary constructors
Here is one of many class with multiple constructors in Java class

```java
public class EventMonitor {

	private final BlockingQueue<StatusEvent> statusEvents;
	private final Map<Integer, PriceMessage> prices;
	private final Map<Integer, ProductData> data;
	private final Map<Integer, DateTime> updates;
	private final Map<Integer, DateTime> dataUpdates;
	private final Map<Class, AtomicLong> counters;
	private final Map<Class, DateTime> messageUpdates;
	private final EventTracer eventTracer;
	private final Service service;
	private final AtomicBoolean activated;
	private final boolean debug;
	private final int capacity;

	public EventMonitor(Service service, EventTracer eventTracer) {
		this(service, eventTracer, false);
	}

	public EventMonitor(Service service, EventTracer eventTracer, boolean debug) {
		this(service, eventTracer, debug, 100);
	}

	public EventMonitor(Service service, EventTracer eventTracer, boolean debug, int capacity) {
		this.prices = new ConcurrentHashMap<Integer, PriceMessage>();
		this.data = new ConcurrentHashMap<Integer, ProductData>();
		this.dataUpdates = new ConcurrentHashMap<Integer, DateTime>();
		this.updates = new ConcurrentHashMap<Integer, DateTime>();
		this.counters = new ConcurrentHashMap<Class, AtomicLong>();
		this.messageUpdates = new ConcurrentHashMap<Class, DateTime>();
		this.statusEvents = new LinkedBlockingQueue<StatusEvent>();
		this.activated = new AtomicBoolean();
		this.eventTracer = eventTracer;
		this.capacity = capacity;
		this.service = service;
		this.debug = debug;
	}

}
```

This could be converted to following Kotlin version , the first line is primary constructor while followings are different variant of so called secondary constructor.

```java
class EventMonitor(service: Service?, eventTracer: EventTracer?, debug: Boolean, capacity: Int) {
    constructor(service: Service?, eventTracer: EventTracer?) : this(service, eventTracer, false) {}
    constructor(service: Service?, eventTracer: EventTracer?, debug: Boolean) : this(service, eventTracer, debug, 100) {}
```

#### Immutable! 

   - Read-only list
```java
val list = listOf("a", "b", "c")
```
   - Read-only map
```java
val map = mapOf("a" to 1, "b" to 2, "c" to 3)
```

### `Sugars! Syntax` sugars and plenty of out-of-box utilities

Those syntax sugar or built-in functions are not only lead to shorter code but also increased readability.  Developers would love it.

   - Checking element presence in a collection.

```java
if ("john@example.com" in emailsList) { ... }
if ("jane@example.com" !in emailsList) { ... }
```

   - Lots of functions for Collections

```java
// Kotlin
val numOfAdults = list.count {it.age > 18 }

// Counterpart version in Java. It still be lengthy even in Lambda
int numOfAdults = (int) list.stream().filter(person -> person.age>18).count()


// Kotlin
val map = mapOf("firstName" to "John", "lastName" to "Doe")

//Java, lots of ceremony, so lots of people import 3rd party library
import com.google.common.collect.ImmutableMap;
...

Map<String, String> string = ImmutableMap.of("firstName", "John", "lastName", "Doe");
```

   - Two lists are considered equal if they have the same sizes and structurally equal elements at the same positions.
```java
val bob = Person("Bob", 31)
val people = listOf(Person("Adam", 20), bob, bob)
val people2 = listOf(Person("Adam", 20), Person("Bob", 31), bob)
println(people == people2)
bob.age = 32
println(people == people2)
```
