---
layout: page
title: Default feature in Java 8
tag:
- Coding
- Java
---

# **default** in Java

## There are three rules about **default**
Regarding how to handle the situation of same default method in multiple inheritance.
- **class win**, any class wins over any interfaces.So if there’s a method with a body, or an abstract declaration, in the superclass chain, we can ignore the interfaces completely.
- **subtype win supertype**, “which two interfaces are competing to provide a default method and one interface extends the other, the subclass wins.”
- **No rule 3**. if the previous two rules don't give us the answer, the subclass must either implement the method or declare it **abstract**.

“Interfaces give you multiple inheritance but no fields, while abstract classes let you “inherit fields but you don’t get multiple inheritance.”

# Static method in Interface

We’ve seen a lot of calling of **Stream.of** but haven’t gotten into its details yet. You may recall that Stream is an interface, but this is a static method on an interface. 
```java
stream.collect(toCollection(TreeSet::new));
```


# **Optional** is a better of **null**
```java
//Optional can be created via factory method 'of', 
Optional<String> a = Optional.of("a");
// Optional is just a container, you can get the underlying value by 'get' method
assertEquals("a", a.get());

// at the meanwhile, Optional can represent 'absent'
// factory method empty or ofNullable from a nullable object can be used
@Test
    public void testOptional(){
        Optional<String> optA=Optional.of("a");
        Assert.assertEquals("a", optA.get());
    }
    
    @Test
    public void testEmpty(){
        Optional emp=Optional.ofNullable(null);
        Assert.assertEquals(Optional.empty(), emp);
        Assert.assertFalse(emp.isPresent());
        Assert.assertEquals("b", emp.orElse("b"));
        Assert.assertEquals("c", emp.orElseGet(()->"c"));
    }
```

# method reference
- ** Classname::methodname** , such as Artist::getName is equivalant to artist->artist.getName()
- For constructors can be used Artist::new
- You can alos to create new array, String[]::new

# Stream
“The purpose of streams isn’t just to convert from one collection to another; it’s to be able to provide a common set of operations over data.”

