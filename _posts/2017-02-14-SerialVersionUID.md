---
layout: posts
title: SeriableVersionUID
tags:
- java
- serialVersionUID
---
# Noteworthy points about SeriableVersionUID in Java

## Preventing ClassCastExceptions with SerialVersionUID Problem
- Your classes were recompiled, and you’re getting ClassCastExceptions that you shouldn’t.
Solution
- Run serialver to generate a “serial version UUID” and paste its output into your classes before you start. Or use your IDE’s tools for this purpose.
Discussion
- When a class is undergoing a period of evolution—particularly a class being used in a networking context such as RMI or servlets—it may be useful to provide a serialVersionUID value in this class. This is a long that is basically a hash of the methods and fields in the class. Both the object serialization API (see Saving and Restoring Java Objects) and the JVM, when asked to cast one object to another (common when using collections, as in Chapter 7), either look up or, if not found, compute this value. If the value on the source and destination do not match, a ClassCastException is thrown. Most of the time, this is the correct thing for Java to do.
However, sometimes you may want to allow a class to evolve in a compatible way, but you can’t immediately replace all instances in circulation. You must be willing to write code to account for the additional fields being discarded if restoring from the longer format to the shorter and having the default value (null for objects, 0 for numbers, and false for Boolean) if you’re restoring from the shorter format to the longer. If you are only adding fields and methods in a reasonably compatible way, you can control the compatibility by providing a long int named serialVersionUID. The initial value should be obtained from a JDK tool called serialver, which takes just the class name. Consider a simple class called SerializableUser:
```java
public class SerializableUser implements java.io.Serializable {
    public String name;
    public String address;
    public String country;
    public String phoneNum;

    // other fields, and methods, here...
    static final long serialVersionUID = -7978489268769667877L;
}
```
I first compiled it with two different compilers to ensure that the value is a product of the class structure, not of some minor differences in class file format that different compilers might emit:
```sh
$ javac SerializableUser.java
$ serialver SerializableUser
SerializableUser:    static final long serialVersionUID = -7978489268769667877L;
$ jikes +E SerializableUser.java
$ serialver SerializableUser
SerializableUser:    static final long serialVersionUID = -7978489268769667877L;
```
Sure enough, the class file from both compilers has the same hash. Now let’s change the file. I go in with an editor and add a new field, phoneNum, right after country:
```java
 public String country;
public String phoneNum;      // Added this line.
```

```sh
$ javac SerializableUser.java
$ serialver SerializableUser
SerializableUser:    static final long serialVersionUID = -8339341455288589756L;
```
Notice how the addition of the field changed the serialVersionUID! Now, if I had wanted this class to evolve in a compatible fashion, here’s what I should have done before I started expanding it. I copy and paste the original serialver output into the source file (again using an editor to insert a line before the last line):
```java
 // The following is the line I added to SerializableUser.java
private static final long serialVersionUID = -7978489268769667877L;  
```

```sh
$ javac SerializableUser.java
$ serialver SerializableUser
SerializableUser:    static final long serialVersionUID = -7978489268769667877L;
$
```
- Now all is well: I can interchange serialized versions of this file.
Note that serialver is part of the “object serialization” mechanism, and, therefore, it is meaningful only on classes that implement the Serializable interface described in Saving and Restoring Java Objects.
Note also that some developers use serialVersionUID values that start at 1 (a choice offered by some IDEs when they note that a class that appears to be serializable lacks a serialVersionUID), and then simply increment it by one each time the class changes in an incompatible way.
