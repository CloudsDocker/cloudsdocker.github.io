 ---
 layout: page
 title: java Security
 tags:
 - java
 - Security
 ---

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
