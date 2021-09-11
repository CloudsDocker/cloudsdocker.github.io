---
layout: posts
title: Compare-In-Java
tags:
- java
- compare
---

# Concepts
- If you implement Comparable interface and override compareTo() method it **must be consistent with equals()** method i.e. for equal object by equals() method compareTo() must return zero. failing to so will affect contract of SortedSet e.g. TreeSet and SortedMap like TreeMap, which uses compareTo() method for checking equality
- Remember to use Collections.reverseOrder() comparator for sorting Object in reverse order or descending order, as shown in this example.
- Use Generics while implementing Comparator and Comparable interface, that prevents error of accidentally overloading compareTo() and compare() method instead of overriding it because both of these methods accept Object as a parameter. By using Generics and @Override annotation we effectively remove that subtle error.

# Comparable vs Comparator
1. Comparator in Java is defined in java.util package while Comparable interface in Java is defined in java.lang package, which very much says that Comparator should be used as an utility to sort objects which Comparable should be provided by default
1. Comparator interface in Java has method public int compare (Object o1, Object o2) which returns a negative integer, zero, or a positive integer as the first argument is less than, equal to, or greater than the second. While Comparable interface has method public int compareTo(Object o) which returns a negative integer, zero, or a positive integer as this object is less than, equal to, or greater than the specified object.
1. If any class implement Comparable interface in Java then collection of that object either List or Array can be sorted automatically by using  Collections.sort() or Arrays.sort() method and object will be sorted based on there natural order defined by CompareTo method.
1. Objects which implement Comparable in Java  can be used as keys in a SortedMap like TreeMap or elements in a SortedSet  for example TreeSet, without specifying any Comparator.
1. Generally you should not use difference of integers to decide output of compareTo method as result of **integer subtraction can overflow ** but if you are sure that both operands are positive then its one of the quickest way to compare two objects. 
1. Some time you write code to sort object of a class for which you are not the original author, or you don't have access to code. In these cases you can not implement Comparable and Comparator is only way to sort those objects.
1. Beware with the fact that How those object will behave if stored in SorteSet or SortedMap like TreeSet and TreeMap. If an object doesn't implement Comparable than while putting them into SortedMap, always provided corresponding Comparator which can provide sorting logic.
1. Comparator has a distinct advantage of being self descriptive  for example if you are writing Comparator to compare two Employees based upon there salary than name that comparator as SalaryComparator, on the other hand compareTo()

So in Summary if you want to sort objects based on **natural order then use Comparable** in Java and if you want to **sort on some other attribute of object then use Comparator ** in Java.

# Samples of Java class
- How to Compare String in Java
String is immutable in Java and one of the most used value class. For comparing String in Java we should not be worrying because String implements Comparable interface and provides a lexicographic implementation for CompareTo method which compare two strings based on contents of characters or you can say in lexical order. You just need to call String.compareTo(AnotherString) and Java will determine whether specified String is greater than , equal to or less than current object. 
- Dates are represented by java.util.Date class in Java and like String,  Date also implements Comparable in Java so they will be automatically sorted based on there natural ordering if they got stored in any sorted collection like TreeSet or TreeMap. If you explicitly wants to compare two dates in Java you can call Date.compareTo(AnotherDate) method in Java and it will tell whether specified date is greater than , equal to or less than current String.

# Exceptions

One example where compareTo is not consistent with equals in JDK is BigDecimal class. two BigDecimal number for which compareTo returns zero, equals returns false as clear from following BigDecimal comparison example:
```java
BigDecimal bd1 = new BigDecimal("2.0");
BigDecimal bd2 = new BigDecimal("2.00");

System.out.println("comparing BigDecimal using equals: " + bd1.equals(bd2));
System.out.println("comparing BigDecimal using compareTo: " + bd1.compareTo(bd2));

Output:

comparing BigDecimal using equals: false
comparing BigDecimal using compareTo: 0
```
 How does it affect BigDecimal ? well if you store these two BigDecimal in HashSet you will end up with duplicates (violation of Set Contract) i.e. two elements while if you store them in TreeSet you will end up with just 1 element because HashSet uses equals to check duplicates while TreeSet uses compareTo to check duplicates. That's why its suggested to keep compareTo consistent with equals method in java.

- Another important point to note is don't use subtraction for comparing integral values because result of subtraction can overflow as every int operation in Java is modulo 2^32. use either Integer.compareTo()  or logical operators for comparison. 
-  In summary compareTo should provide natural ordering and compareTo must be consistent with equals() method in Java. 
 
 

```java
package test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 *
 * Java program to test Object sorting in Java. This Java program
 * test Comparable and Comparator implementation provided by Order
 * class by sorting list of Order object in ascending and descending order.
 * Both in natural order using Comparable and custom Order using Comparator in Java
 *
 * @author http://java67.blogspot.com
 */
public class ObjectSortingExample {

    public static void main(String args[]) {
     
        //Creating Order object to demonstrate Sorting of Object in Java
        Order ord1 = new Order(101,2000, "Sony");
        Order ord2 = new Order(102,4000, "Hitachi");
        Order ord3 = new Order(103,6000, "Philips");
     
        //putting Objects into Collection to sort
        List<Order> orders = new ArrayList<Order>();
        orders.add(ord3);
        orders.add(ord1);
        orders.add(ord2);
     
        //printing unsorted collection
        System.out.println("Unsorted Collection : " + orders);
     
        //Sorting Order Object on natural order - ascending
        Collections.sort(orders);
     
        //printing sorted collection
        System.out.println("List of Order object sorted in natural order : " + orders);
     
        // Sorting object in descending order in Java
        Collections.sort(orders, Collections.reverseOrder());
        System.out.println("List of object sorted in descending order : " + orders);
             
        //Sorting object using Comparator in Java
        Collections.sort(orders, new Order.OrderByAmount());
        System.out.println("List of Order object sorted using Comparator - amount : " + orders);
     
        // Comparator sorting Example - Sorting based on customer
        Collections.sort(orders, new Order.OrderByCustomer());
        System.out.println("Collection of Orders sorted using Comparator - by customer : " + orders);
    }
}

/*
 * Order class is a domain object which implements
 * Comparable interface to provide sorting on the natural order.
 * Order also provides couple of custom Comparators to
 * sort object based upon amount and customer
 */
class Order implements Comparable<Order> {

    private int orderId;
    private int amount;
    private String customer;

    /*
     * Comparator implementation to Sort Order object based on Amount
     */
    public static class OrderByAmount implements Comparator<Order> {

        @Override
        public int compare(Order o1, Order o2) {
            return o1.amount > o2.amount ? 1 : (o1.amount < o2.amount ? -1 : 0);
        }
    }

    /*
     * Anohter implementation or Comparator interface to sort list of Order object
     * based upon customer name.
     */
    public static class OrderByCustomer implements Comparator<Order> {

        @Override
        public int compare(Order o1, Order o2) {
            return o1.customer.compareTo(o2.customer);
        }
    }

    public Order(int orderId, int amount, String customer) {
        this.orderId = orderId;
        this.amount = amount;
        this.customer = customer;
    }

 
    public int getAmount() {return amount; }
    public void setAmount(int amount) {this.amount = amount;}

    public String getCustomer() {return customer;}
    public void setCustomer(String customer) {this.customer = customer;}

    public int getOrderId() {return orderId;}
    public void setOrderId(int orderId) {this.orderId = orderId;}

    /*
     * Sorting on orderId is natural sorting for Order.
     */
    @Override
    public int compareTo(Order o) {
        return this.orderId > o.orderId ? 1 : (this.orderId < o.orderId ? -1 : 0);
    }
 
    /*
     * implementing toString method to print orderId of Order
     */
    @Override
    public String toString(){
        return String.valueOf(orderId);
    }
}

Output
Unsorted Collection : [103, 101, 102]
List of Order object sorted in natural order : [101, 102, 103]
List of object sorted in descending order : [103, 102, 101]
List of Order object sorted using Comparator - amount : [101, 102, 103]
Collection of Orders sorted using Comparator - by customer : [102, 103, 101]


```

# Reference 
- http://www.java67.com/2012/10/how-to-sort-object-in-java-comparator-comparable-example.html
