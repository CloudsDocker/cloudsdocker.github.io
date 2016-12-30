
# contract of hashCode :

- Whenever it is **invoked on the same object more than once during an execution of a Java application, the hashCode method must consistently return the same integer**, provided no information used in equals comparisons on the object is modified. This _integer need **not** remain consistent from one execution of an application to another execution of the **same** application_.
- If two objects **are equal** according to the equals(Object) method, then calling the hashCode method on each of the two objects must produce the **same integer** result.
- It is **not required** that **if two objects are unequal** according to the equals(java.lang.Object) method, then calling the hashCode method on each of the two objects **must produce distinct integer results**. However, the programmer should be aware that producing distinct integer results for unequal objects _may improve the performance of hash tables_.

As much as is reasonably practical, the hashCode method defined by class Object does return distinct integers for distinct objects. (This is typically implemented by **converting the internal address** of the object into an integer, but this implementation technique is not required by the JavaTM programming language.)
