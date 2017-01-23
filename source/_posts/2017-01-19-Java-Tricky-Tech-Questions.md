---
layout: page
title: Java-Tricky-Tech-Questions.md
tags:
- java
- Questions
---
# Question: What does the following Java program print?

public class Test {
    public static void main(String[] args) {
        System.out.println(Math.min(Double.MIN_VALUE, 0.0d));
    }
}

## Anwser 0.0d
The Double.MIN_VALUE is 2^(-1074), a double constant whose magnitude is the least among all double values. 


# What will happen if you put return statement or System.exit () on try or catch block? Will finally block execute?
Answer of this tricky question in Java is that **finally block will execute even if you put a return statement** in the try block or catch block but finally block **won't run if you call System.exit()** from try or catch block. 

# Question: Can you override a private or static method in Java?

Another popular Java tricky question, As I said method overriding is a good topic to ask trick questions in Java. Anyway, you **can not override a private or static method** in Java, if you **create a similar method with same return type and same method arguments in child class** then it will **hide the superclass method**, this is known as **method hiding**.

Similarly, you cannot override a private method in sub class because it's not accessible there, what you do is create another private method with the same name in the child class. See Can you override a private method in Java or more details

# Question: What do the expression 1.0 / 0.0 will return? will it throw Exception? any compile time error?

Answer: This is another tricky question from Double class. Though Java developer knows about the double primitive type and Double class, while doing floating point arithmetic they don't pay enough attention to Double.INFINITY , NaN, and -0.0
and other rules that govern the arithmetic calculations involving them. The simple answer to this question is that it will not throw ArithmeticExcpetion and **return Double.INFINITY**.

Also, note that the comparison **x == Double.NaN always evaluates to false**, even if x itself is a NaN. To test if x is a NaN, one should use the method call Double.isNaN(x) to check if given number is NaN or not. If you know SQL, this is very close to NULL there. 


# Overloading vs Overriding
- Main difference comes from the fact that method **overloading is resolved during compile time**, while method **overriding is resolved at runtime**
- Also rules of overriding or overloading a method are different in Java. 
   - a private, static and final method cannot be overriding in Java but you can still overload them
   - overriding both name and signature of the method must remain same, but in for overloading method, the signature must be different
   - call to **overloaded** methods are **resolved using static binding** while the call to **overridden method is resolved using dynamic binding** in Java.
- Java programmer to declare method with same name but different behavior. Method overloading and method overriding is based on Polymorphism in Java.
- In case of method overloading, method with same name co-exists in **same class** but they must have **different method signature**, while in case of method **overriding**, method with **same name** is declared in **derived class or sub class**
- If you have **two methods with same name** in one Java class **with different method signature** than its called **overloaded** method in Java. You can also overload constructor in Java
- Since **return type is not part of method signature** simply changing return type will result in duplicate method and you will get compile time error in Java.
- you can also **overload private and final method** in Java but you **can not override** them
- When you **override a method** in Java its signature remains exactly same **including return type**. Rules of override:
   - Method signature must be same including return type, number of method parameters, type of parameters **and order of parameters** . Be advised: as of Java 5, you're allowed to change the return type in the overriding method as long as the new return type is a subtype of the declared return type of the overridden (super class) method
   - Overriding method **can not throw higher Exception** than original or overridden method. means if original method throws IOException than overriding method can not throw super class of IOException e.g. Exception but it can throw any sub class of IOException or simply does not throw any Exception. This rule only applies to checked Exception in Java, overridden method is free to throw any unchecked Exception. 
   - Overriding method **can not reduce accessibility of overridden method** , means if original or overridden method is public than overriding method **can not make it protected**. 
- Another important point is that you **can not override static method** in Java because **they are associated with Class** **rather than object** and resolved and **bonded during compile time** and that’s the reason you cannot override main method in Java
- From Java 5 onwards you can use annotation in Java to declare overridden method just like we did with @override. ** @override annotation allows compiler** , IDE like NetBeans and Eclipse **to cross verify or check**  if this method is really overrides super class method or not.


# Static vs. Dynamic binding
- **private, final and static methods and variables uses static binding** and bonded by compiler while **virtual methods** are bonded during **runtime** based upon runtime object.
- Here is sample of static binding 
```java
public class StaticBindingTest {
      public static void main(String args[])  {
       Collection c = new HashSet();
       StaticBindingTest et = new StaticBindingTest();
       et.sort(c);
          }
   
    //overloaded method takes Collection argument
    public Collection sort(Collection c){
        System.out.println("Inside Collection sort method");
        return c;
    }

   //another overloaded method which takes HashSet argument which is sub class
    public Collection sort(HashSet hs){
        System.out.println("Inside HashSet sort method");
        return hs;
    }
      }
Output: Inside Collection sort method
```
**because it was bonded on compile time based on type of variable (Static binding)  which was collection.**

- Here is sample of dynamic binding 
```java
public class DynamicBindingTest {
    public static void main(String args[]) {
        Vehicle vehicle = new Car(); //here Type is vehicle but object will be Car
        vehicle.start();       //Car's start called because start() is overridden method
    }
}

class Vehicle {
    public void start() {
        System.out.println("Inside start method of Vehicle");
    }
}

class Car extends Vehicle {
    @Override
    public void start() {
        System.out.println("Inside start method of Car");
    }
}

Output: Inside start method of Car
```

In summary, bottom line is static binding is a compile time operation while dynamic binding is a runtime. one uses Type and other uses Object to bind. static, private and final methods and variables are resolved using static binding which makes there execution fast because no time is wasted to find correct method during runtime.

# Static in Java
- static keyword can not be applied on top level class. Making a top level class static in Java will result in compile time error.
-  Beware that if your static initialize block throws Exception than you may **get java.lang.NoClassDefFoundError** when you try to access the class which failed to load.
-  **Static method can not be overridden** in Java as they belong to class and not to object
```java
 public class TradingSystem {

    public static void main(String[] args) {
        TradingSystem system = new DirectMarketAccess();
        DirectMarketAccess dma = new DirectMarketAccess();
        
        // static method of Instrument class will be called,

        // even though object is of sub-class DirectMarketAccess
        system.printCategory();
        
        //static method of EquityInstrument class will be called
        dma.printCategory();
    }

    public static void printCategory(){
        System.out.println("inside super class static method");
    }
}

class DirectMarketAccess extends TradingSystem{
    public static void printCategory(){
        System.out.println("inside sub class static method");
    }
}

Output:
inside super class static method
inside sub class static method
```
- This shows that static method can not be overridden in Java and concept of method overloading doesn't apply to static methods. Instead declaring same static method on Child class **is known as method hiding** in Java
- Consider **making a static variable final** in Java to make it constant and avoid changing it from anywhere in the code
- when to use Singleton vs Static Class in Java for those purpose,answer is that if its **completely stateless** and it work on provided data then you can **go for static class** **otherwise Singleton** pattern is a better choice.
## When to make a method static in Java
- Method **doesn't depends on object's state**, in other words **doesn't depend on any member variable** and **everything they need is passes as parameter** to them
- Utility methods are good candidate of making static in Java because then they can directly be accessed using class name without even creating any instance. Classic example is java.lang.Math
- Static method in Java is very popular to implement Factory design pattern. Since Generics also provides type inference during method invocation, use of static factory method to create object is popular Java idiom. 

# Phone interview
-  Key to success in telephonic interview is **to the point** and **concise answer**.

## Difference between String, StringBuffer and StringBuilder in Java
- String is **immutable** while both StringBuffer and StringBuilder **is mutable**, which means any change e.g. converting String to upper case or trimming white space will **produce another instance** rather than changing the same instance. On later two, **StringBuffer is synchronized** while **StringBuilder is not**, in fact its a ditto replacement of StringBuffer added in Java 1.5.
## Difference between extends Thread vs implements Runnable in Java? 
- Difference comes from the fact that you **can only extend one class** in Java, which means if you extend Thread class you lose your opportunity to extend another class, on the other hand if you implement Runnable, you can still extend another class.

## Difference between Runnable and Callable interface in Java? 
- Runnable was the only way to implement a task in Java which can be executed in parallel before JDK 1.5 adds Callable. Just like Runnable, Callable also defines a single **call() method** but unlike run() it **can return values and throw exceptions**.

## Difference between ArrayList and LinkedList in Java? 
- In short, ArrayList is backed by array in Java, while **LinkedList is just collection of nodes**, similar to linked list data structure. ArrayList also provides **random search** if you know the index, while **LinkedList only allows sequential search**. On other hand, **adding and removing element from middle** is **efficient in LinkedList** as compared to ArrayList because it only require to modify links and no other element is rearranged.

## What is difference between wait and notify in Java? 
- Both wait and notify methods are used for **inter thread communication**, where **wait is used to pause** the thread on a condition and **notify is used to send notification** to waiting threads. Both must be called from synchronized context e.g. **synchronized method or block**.


## Difference between HashMap and Hashtable in Java? 
- Though both HashMap and Hashtable are based upon hash table data structure, there are subtle difference between them. HashMap is non synchronized while Hashtable is synchronized and because of that HashMap is faster than Hashtable, as there is no cost of synchronization associated with it. One more minor difference is that HashMap allows a null key but Hashtable doesn't.





# Reference 
- http://www.java67.com/2012/09/top-10-tricky-java-interview-questions-answers.html
- http://javarevisited.blogspot.in/2012/03/what-is-static-and-dynamic-binding-in.html
- http://www.java67.com/2015/03/top-40-core-java-interview-questions-answers-telephonic-round.html
