---
layout: page
title: Java Security Notes
tags:
- java
- security
---

# Java Security
- `well-behaved`: programs should be prevent from consuming too much system resources

## Components
- JCE: Java Cryptography Extension
- JSSE: Java Secure Socketets Extension
- JAAS: Java Authentication and Authorization Service

# Anatomy of a Java Application
## the bytecode verifier
The bytecode verifier ensures that Java class files follow the rules of the Java language. As the figure implies, not all classes are subject to bytecode verification.
## the class loader
One or more class loaders load all Java classes. Programatically, the class loader can set permissions for each class it loads.
## the access controller
The access controller allows (or prevents) most access from the core API to the operating system, based upon policies set by the end user or system administrator.
## the security manager
The security manager is the primary interface between the core API and the operating system; it has the ultimate responsibility for allowing or preventing access to all system resources. However, it exists mostly for historical reasons; it defers its actions to the access controller.
## The security package
 the security package is a complex API and discussion of it is broken into several chapters of this book. This includes discussions of:
- The security provider interface −− the means by which different security implementations may be plugged into the security package
- Message digests
- Keys and certificates
- Digital signatures
- Encryption (through JCE and JSSE)
- Authentication (through JAAS)

## The key database
The key database is a set of keys used by the security infrastructure to create or verify digital signatures. In the Java architecture, it is part of the security package, though it may be manifested as an external file or database.

## Trusted and Untrusted Classes
- In Java 2, only classes in the core API are considered trusted. Other classes must be given explicit permission to perform the operations we've discussed.

## Summary
Although the security manager is the most commonly known feature of Java's security story, it's often misunderstood: there is no standard security manager among Java implementations, and Java applications, by default, have no security manager at all.


# Access Controller
- The implementation of most security managers, however, is based entirely upon the access controller.

## Permissions
- The basic entity that the access controller operates on is a permission object −− an instance of the Permission class (java.security.Permission). This class, of course, is the basis of the types that are listed in a policy file for the default security policy. The Permission class itself is an abstract class that represents a particular operation. The nomenclature here is a little misleading because a permission object can reflect two things. When it is associated with a class (through a code source and a protection domain), a permission object represents an actual permission that has been granted to that class. Otherwise, a permission object allows us to ask if we have a specific permission.
- For example, if we construct a permission object that represents access to a file, possession of that object does not mean we have permission to access the file. Rather, possession of the object allows us to ask if we have permission to access the file.


## The access controller is built upon the four concepts
- Code sources
An encapsulation of the location from which certain Java classes were obtained.
- Permissions
An encapsulation of a request to perform a particular operation.
- Policies
An encapsulation of all the specific permissions that should be granted to specific code sources.
- Protection domains
An encapsulation of a particular code source and the permissions granted to that code source.























