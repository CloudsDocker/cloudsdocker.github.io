---
title: Guice
layout: posts
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



Guice aims to eliminate all of this boilerplate without sacrificing maintainability.
With Guice, you implement modules. Guice passes a binder to your module, and your module uses the binder to map interfaces to implementations. The following module tells Guice to map Service to ServiceImpl in singleton scope:
```java
       public class MyModule implements Module {
         public void configure(Binder binder) {
          binder.bind(Service.class)
           .to(ServiceImpl.class)
           .in(Scopes.SINGLETON);
} }
```

A module tells Guice what we want to inject. Now, how do we tell Guice where we want it injected? With Guice, you annotate constructors, methods and fields with @Inject.
```java
       public class Client {
         private final Service service;
@Inject
         public Client(Service service) {
           this.service = service;
}
         public void go() {
           service.go();
} }
```

## Guice vs. Dependency Injection By Hand
As you can see, Guice saves you from having to write factory classes. You don't have to write explicit code wiring clients to their dependencies. If you forget to provide a dependency, Guice fails at startup. Guice handles circular dependencies automatically.
Guice enables you to specify scopes declaratively. For example, you don't have to write the same code to store an object in the HttpSession over and over.
In the real world, you often don't know an implementation class until runtime. You need meta factories or service locators for your factories. Guice addresses these problems with minimal effort.
When injecting dependencies by hand, you can easily slip back into old habits and introduce direct dependencies, especially if you're new to the concept of dependency injection. Using Guice turns the tables and makes doing the right thing easier. Guice helps keep you on track.

## Guice annotations
When possible, Guice enables you to use annotations in lieu of explicit bindings and eliminate even more boilerplate code. Back to our example, if you need an interface to simplify unit testing but you don't care about compile time dependencies, you can point to a default implementation directly from your interface.
```java
       @ImplementedBy(ServiceImpl.class)
       public interface Service {
         void go();
}
```

If a client needs a Service and Guice can't find an explicit binding, Guice will
inject an instance of ServiceImpl.

By default, Guice injects a new instance every time. If you want to specify a
different scope, you can annotate the implementation class, too.
```java
@Singleton
       public class ServiceImpl implements Service {
         public void go() {
... }
}
```

# Architectural Overview
We can break Guice's architecture down into two distinct stages: startup and
runtime. You build an Injector during startup and use it to inject objects at runtime.

## Startup
You configure Guice by implementing Module. You pass Guice a module, Guice passes your module a Binder, and your module uses the binder to configure bindings. A binding most commonly consists of a mapping between an interface and a concrete implementation. For example:
```java
       public class MyModule implements Module {
         public void configure(Binder binder) {
          // Bind Foo to FooImpl. Guice will create a new
           // instance of FooImpl for every injection.
           binder.bind(Foo.class).to(FooImpl.class);
           // Bind Bar to an instance of Bar.
           Bar bar = new Bar();
           binder.bind(Bar.class).toInstance(bar);
}
```


# Injecting Providers
With normal dependency injection, each type gets exactly one instance of each of its dependent types. The RealBillingService gets one CreditCardProcessor and one TransactionLog. Sometimes you want more than one instance of your dependent types. When this flexibility is necessary, Guice binds a provider. Providers produce a value when the get() method is invoked:
```java
public interface Provider<T> {
  T get();
}
```

# @Provides Methods
When you need code to create an object, use an @Provides method. The method must be defined within a module, and it must have an @Provides annotation. The method's return type is the bound type. Whenever the injector needs an instance of that type, it will invoke the method.
```java
public class BillingModule extends AbstractModule {
  @Override
  protected void configure() {
    ...
  }

  @Provides
  TransactionLog provideTransactionLog() {
    DatabaseTransactionLog transactionLog = new DatabaseTransactionLog();
    transactionLog.setJdbcUrl("jdbc:mysql://localhost/pizza");
    transactionLog.setThreadPoolSize(30);
    return transactionLog;
  }
}
```
If the @Provides method has a binding annotation like @PayPal or @Named("Checkout"), Guice binds the annotated type. Dependencies can be passed in as parameters to the method. The injector will exercise the bindings for each of these before invoking the method.
```java
  @Provides @PayPal
  CreditCardProcessor providePayPalCreditCardProcessor(
      @Named("PayPal API key") String apiKey) {
    PayPalCreditCardProcessor processor = new PayPalCreditCardProcessor();
    processor.setApiKey(apiKey);
    return processor;
  }
```


# References
