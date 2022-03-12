---
header:
    image: /assets/images/hd_groovy.jpg
title:  Everything you'd know for Groovy interviews
date: 2022-03-12
tags:
 - Groovy
 - Java
 - Programing
 
permalink: /blogs/tech/en/ace_in_groovy_interview
layout: single
category: tech
---

> Life is short. Don't waste it with negative people who don't appreciate you. Keep them in your heart but keep them out of your life.


# Call functions in primitive variable
One difference to Java, you can invoke function on primitive variables, e.g. call method `plus` on int as below

```java
class test {
    static void main(String[] args){
        println("3+5="+(3.plus(5)))
    }
}
```

# Accurate calculation on float number
In Java, as you know the calculation of float number is inaccurate, if you need such accuracy, you'll have to use `BigDecimal` or others. 
However, it's not a problem in Groovy.

```java
def num1=1.000000000001
def num2=2.000000000002
println(num1+"+"+num2+"="+num1.plus(num2))
```

And output is:

```
BearSuperBrain:groovy todzhang$ groovy test.groovy 
start
3+5=8
1.000000000001+2.000000000002=3.000000000003
```

## generate random number within 100
Using combination of nextInt and division of 100

```java
println("next random number:"+(Math.abs(new Random().nextInt())%100))

```

## Variable placeholder

```java
def name="todd"
println("hello $name")
```

## String literals 

Use *3 single quote * for string in multiple lines

```java
def body='''
    hello
        nice to see you
        bye
    '''
println("the message body is $body")
```

## String computation
You can *multiply* and *subtract* on `Groovy String`

```java
def greeting="hello world to you"*2
println(greeting-"hello")
```

### String comparator <=>
This will return 0 if two strings are equals and -1 if former string is before the 2nd string, otherwise return +1

Following will get `-1` in output as the *str1* comes before *str2*
```java
def str1="book"
def str2="boot" 
println("str1<=>str2:"+(str1<=>str2))
```

## Get chars from String by index
Similar to `charAt` in Java String, you can access each characters easily in *Groovy*

```java
def name="todd"
println("hello $name")
println("first 3 chars are:"+name[0..2])
println(" chars are:"+name[0,2,3])
```

# List & Array

## Array of multiple data types
In Groovy, you can assign different type of values into an array, it like a data class in Java.

```java
def book=[12345,5.99,"How to coding in Groovy",[10,20,30]]
println("2nd number is:"+book[3][1])
```

## To add & substract in Array
You can use various operators such as `add`, `+`, `<<`
 Take below sample

 ```java
book.add(55)
book<<66
book=book+[77,88]
println(book)
book=book-[55]
println(book)
 ```

# Map
## To add, update entries in Map

Map is another type of List which is key value pair

```java
def states=[
    'capital':'Sydney',
    'population': 5_000_000
]
 
println('capital is:'+states['capital'])
states.put('flower','Rose')
states.put('capital','Unknown')

println(states.get('capital')+", flower is:"+states.get('flower'))
```


--End--



