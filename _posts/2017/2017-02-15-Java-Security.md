---
layout: posts
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
 the security package is a complex API. This includes discussions of:
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

# Byte code verifier
- The verifier is often referred to as a `mini−theorem prover` (a term first used in several documents from Sun). This sounds somewhat more impressive than it is; it's not a generic, all−purpose theorem prover by any means. Instead, it's a piece of code that can prove one (and only one) thing −− that a given series of ( Java) bytecodes represents a legal set of ( Java) instructions.

# Shifting
Java and JavaScript perform sign extension when shift¬ing right, filling the empty spaces with 1’s for negative numbers, so 10100110 >> 5 becomes 11111101.
The >>> operator is unique to Java and JavaScript. It does a logical shift right, filling the empty spaces with 0 no matter what the value, so 10100110 >>> 5 becomes 00000101.

The shift operators enable you to multiply and divide by powers of 2 very quickly. For non-negative numbers, shifting to the right one bit is equivalent to dividing by 2, and shifting to the left one bit is equivalent to multiplying by 2. For negative numbers, it obviously depends on the language being used.


## Specifically, the bytecode verifier can prove the following:
- The class file has the correct format. The full definition of the class file format may be found in the Java virtual machine specification; the bytecode verifier is responsible for making sure that the class file has the right length, the correct magic numbers in the correct places, and so on.
- Final classes are not subclassed, and final methods are not overridden.
- Every class (except for java.lang.Object) has a single superclass.
- There is no illegal data conversion of primitive data types (e.g., int to Object).
- No illegal data conversion of objects occurs. Because the casting of a superclass to its subclass may
be a valid operation (depending on the actual type of the object being cast), the verifier cannot ensure that such casting is not attempted −− it can only ensure that before each such attempt is made, the legality of the cast is tested.
- There are no operand stack overflows or underflows.

## Stacks
- 
In Java, there are two stacks for each thread. One stack holds a series of method frames, where each method frame holds the local variables and other storage for a particular method invocation. This stack is known as the data stack and is what we normally think of as the stack within a traditional program. The bytecode verifier cannot prevent overflow of this stack −− an infinitely recursive method call will cause this stack to overflow. However, each method invocation requires a second stack (which itself is allocated on the data stack) that is referred to as the operand stack; the operand stack holds the values that the Java bytecodes operate on. This secondary stack is the stack that the bytecode verifier can ensure will not overflow or underflow.

# Security Manager
- The implementation of the sandbox depends on three things:
- The security manager, which provides the mechanism that the Java API uses to see if security−related operations are allowed.
- The access controller, which provides the basis of the default implementation of the security manager. 
- The class loader, which encapsulates information about security policies and classes.


We'll start by examining the security manager. From the perspective of the Java API, there is a security manager that actually is in control of the security policy of an application. The purpose of the security manager is to determine whether particular operations should be permitted or denied. In truth, the purpose of the access controller is really the same: it decides whether access to a critical system resource should be permitted or denied. Hence, the access controller can do everything the security manager can do.


**The reason there is both an access controller and a security manager is mainly historical**: the access controller is only available in Java 2 and subsequent releases. Before the access controller existed, the security manager relied on its internal logic to determine the security policy that should be in effect, and changing the security policy required changing the security manager itself. Starting with Java 2, the security manager defers these decisions to the access controller. Since the security policy enforced by the access controller can be specified by using policy files, this allows a much more flexible mechanism for determining policies. The access controller also gives us a much simpler method of granting fine−grained, specific permissions to specific classes. That process was theoretically possibly with the security manager alone, but it was simply too hard to implement.

## The BasicPermission class
- If you need to implement your own permission class, the BasicPermission class (java.security.BasicPermission) provides some useful semantics. This class implements a basic permission −− that is, a permission that doesn't have actions. Basic permissions can be thought of as binary permissions −− you either have them or you don't. However, this restriction does not prevent you from implementing actions in your subclasses of the BasicPermission class (as the PropertyPermission class does).
- The prime benefit of this class is the manner in which it implements wildcards. Names in basic permissions are considered to be hierarchical, following a dot−separated convention. For example, if the XYZ corporation wanted to create a set of basic permissions, they might use the convention that the first word of the permission always be xyz: xyz.readDatabase, xyz.writeDatabase, xyz.runPayrollProgram, xyz.HRDepartment.accessCheck, and so on. These permissions can then be specified by their full name, or they can be specified with an asterisk wildcard: xyz.* would match each of these (no matter what depth), and * would match every possible basic permission.

- http://www.qidianlife.com/index.php?m=home&c=discover&a=article&id=2351

- 保护密码的最好办法是使用加盐密码哈希（ salted password hashing）。
- 永远不要告诉用户输错的究竟是用户名还是密码。就像通用的提示那样，始终显示：“无效的用户名或密码。”就行了。这样可以防止攻击者在不知道密码的情况下枚举出有效的用户名。
- 应当注意的是，用来保护密码的哈希函数，和数据结构课学到的哈希函数是不同的。例如，实现哈希表的哈希函数设计目的是快速查找，而非安全性。只有加密哈希函数（ cryptographic hash function）才可以用来进行密码哈希加密。像 SHA256 、 SHA512 、 RIPEMD 和 WHIRLPOOL 都是加密哈希函数。
- 破解哈希加密最简单的方法是尝试猜测密码，哈希每个猜测的密码，并对比猜测密码的哈希值是否等于被破解的哈希值。如果相等，则猜中。猜测密码攻击的两种最常见的方法是字典攻击和暴力攻击 。

- 字典攻击使用包含单词、短语、常用密码和其他可能用做密码的字符串的字典文件。对文件中的每个词都进行哈希加密，将这些哈希值和要破解的密码哈希值比较。如果它们相同，这个词就是密码。字典文件是通过大段文本中提取的单词构成，甚至还包括一些数据库中真实的密码。还可以对字典文件进一步处理以使其更为有效：如单词 “hello” 按网络用语写法转成 “h3110” 。

- 暴力攻击是对于给定的密码长度，尝试每一种可能的字符组合。这种方式会消耗大量的计算，也是破解哈希加密效率最低的办法，但最终会找出正确的密码。因此密码应该足够长，以至于遍历所有可能的字符组合，耗费的时间太长令人无法承受，从而放弃破解。

- 目前没有办法来组织字典攻击或暴力攻击。只能想办法让它们变得低效。如果密码哈希系统设计是安全的，破解哈希的唯一方法就是进行字典攻击或暴力攻击遍历每一个哈希值了。

- 我们可以通过在密码中加入一段随机字符串再进行哈希加密，这个被加的字符串称之为盐值。如上例所示，这使得相同的密码每次都被加密为完全不同的字符串。我们需要盐值来校验密码是否正确。通常和密码哈希值一同存储在帐号数据库中，或者作为哈希字符串的一部分。

- 盐值无需加密。由于随机化了哈希值，查表法、反向查表法和彩虹表都会失效。因为攻击者无法事先知道盐值，所以他们就没有办法预先计算查询表或彩虹表。如果每个用户的密码用不同的盐再进行哈希加密，那么反向查表法攻击也将不能奏效。

- 一个常见的错误是每次都使用相同的盐值进行哈希加密，这个盐值要么被硬编码到程序里，要么只在第一次使用时随机获得。这样的做法是无效的，因为如果两个用户有相同的密码，他们仍然会有相同的哈希值。攻击者仍然可以使用反向查表法对每个哈希值进行字典攻击。他们只是在哈希密码之前，将固定的盐值应用到每个猜测的密码就可以了。如果盐值被硬编码到一个流行的软件里，那么查询表和彩虹表可以内置该盐值，以使其更容易破解它产生的哈希值。

- 用户创建帐号或者更改密码时，都应该用新的随机盐值进行加密。

- 出于同样的原因，不应该将用户名用作盐值。对每一个服务来说，用户名是唯一的，但它们是可预测的，并且经常重复应用于其他服务。攻击者可以用常见用户名作为盐值来建立查询表和彩虹表来破解密码哈希。

- 为使攻击者无法构造包含所有可能盐值的查询表，盐值必须足够长。一个好的经验是使用和哈希函数输出的字符串等长的盐值。例如， SHA256 的输出为256位（32字节），所以该盐也应该是32个随机字节。

- 每个用户的每一个密码都要使用独一无二的盐值。用户每次创建帐号或更改密码时，密码应采用一个新的随机盐值。永远不要重复使用某个盐值。这个盐值也应该足够长，以使有足够多的盐值能用于哈希加密。一个经验规则是，盐值至少要跟哈希函数的输出一样长。该盐应和密码哈希一起存储在用户帐号表中。

- 存储密码的步骤：
   - 使用 CSPRNG 生成足够长的随机盐值。
   - 将盐值混入密码，并使用标准的密码哈希函数进行加密，如Argon2、 bcrypt 、 scrypt 或 PBKDF2 。
   - 将盐值和对应的哈希值一起存入用户数据库。

- 校验密码的步骤：
   - 从数据库检索出用户的盐值和对应的哈希值。
   - 将盐值混入用户输入的密码，并且使用通用的哈希函数进行加密。
   - 比较上一步的结果，是否和数据库存储的哈希值相同。如果它们相同，则表明密码是正确的；否则，该密码错误。



















