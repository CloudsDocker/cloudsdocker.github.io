---
title: Guice
---

# A new type of Juice
Put simply, Guice alleviates the need for factories and the use of new in your Java code. Think of Guice's @Inject as the new new. You will still need to write factories in some cases, but your code will not depend directly on them. Your code will be easier to change, unit test and reuse in other contexts.

Guice embraces Java's type safe nature, especially when it comes to features introduced in Java 5 such as generics and annotations. You might think of Guice as filling in missing features for core Java. Ideally, the language itself would provide most of the same features, but until such a language comes along, we have Guice.

Guice helps you design better APIs, and the Guice API itself sets a good example. Guice is not a kitchen sink. We justify each feature with at least three use cases. When in doubt, we leave it out. We build general functionality which enables you to extend Guice rather than adding every feature to the core framework.

# Guice vs Spring

Spring and Google Guice are two powerful dependency injection frameworks in use today. Both frameworks fully embrace the concepts of dependency injection, but each has its own way of implementing them. Although Spring provides many benefits, it was created in a pre-Java-5 world. The Guice framework takes DI to the next level.

The advent of Java 5 brought significant changes to the language like generics and annotations: features that enhance the power of Java static typing. Guice is a DI framework that was built from the ground up with the intent to take full advantage of these new features and that has focused on one primary goal: to do dependency injection well.

Guice aims to make development and debugging easier and faster, not harder and slower. In that vein, Guice steers clear of surprises and magic. You should be able to understand code with or without tools, though tools can make things even easier. When errors do occur, Guice goes the extra mile to generate helpful messages.

###  core differences between the two, and see why I prefer to use Guice.

1. Living in XML Hell
2. Eliminating reliance on String identifiers
3. Preferring Constructor Injection

Although Spring and Guice both support constructor and setter injection, each framework has a preference. Spring has long favored setter injection. Back in the early days of Spring, the authors believed the lack of argument names and default arguments in constructor injection reduced clarity. In addition, constructor injection makes it difficult to have optional dependencies, requires dependencies to be configured in a specific order, and forces subclasses to deal with superclass dependencies. Using setter injection eliminates these problems, and so Spring favors that approach.

The Guice authors saw difficulties with setter injection. One problem is immutability: it is impossible to make immutable a class that uses setter injection. Constructor injection, on the other hand, makes the creation of immutable classes easy, an important consideration in writing multi-threaded applications. In addition, optional dependencies, while perhaps convenient, can introduce confusion about how a class is configured at runtime. Configuring a class through setter injection can often lead to missed required dependencies. Though Spring does provide a @Required annotation to solve this problem, using constructor injection eliminates it by default.

Constructor injection also makes a class's dependencies immediately clear at a glance. If you're writing or modifying a unit test, it's easy to read what the system-under-test needs. Lastly, because Guice uses types to wire classes together, constructor argument order isn't an issue. You can feel free to reorder them how you want without needing to modify configuration code at all.

The potential drawbacks posed by setter injection outweigh the benefits in many common scenarios, and so Guice established a best practice of favoring constructor injection instead. Its API is well-suited to that approach. But if you should choose to switch from one form of injection to the other, Guice makes that easy too. Changing from setter to constructor injection or vice versa is simply a matter of modifying the class in question. Unlike in Spring, you need never touch a configuration file.

4. Nullifying NullPointerExceptions

Null is easily one of the most non-communicative return values possible from a method call.
Guice hates nulls as much as I do. By default, Guice refuses to inject a null into any object, and if an accidental null shows up during wiring, it fails-fast with a ProvisionException. Guice does allow for the exception case by permitting fields to be annotated with @Nullable, but this is discouraged.

5. Intruding into the domain

# References
