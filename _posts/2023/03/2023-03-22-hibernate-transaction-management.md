---
title: Hibernate Transaction Management
header:
    image: /assets/images/GoogleMap_missing_JPN.jpg
date: 2023-03-19
tags:
- JFR
- Java
- PerformanceTuning

permalink: /blogs/tech/en/hibernate-transaction-management
layout: single
category: tech
---
# Details of how hibernate transaction management works

Automatic flush: Hibernate will automatically flush any pending changes to the database before executing a query that requires up-to-date data. This can result in entities being saved implicitly. For example:

```java 
Order order = new Order();
order.setItems(items);
entityManager.persist(order);
```

// the following query requires up-to-date data, so Hibernate will flush the pending changes
List<Order> orders = entityManager.createQuery("SELECT o FROM Order o WHERE o.status = 'OPEN'", Order.class).getResultList();
In this example, the Order entity is persisted implicitly when Hibernate flushes the pending changes before executing the query.

Note that while implicit saving can be convenient in some cases, it can also lead to unexpected behavior and performance issues, especially when dealing with large object graphs. It's generally a good practice to be explicit about what you save and when, and to avoid relying on implicit behavior whenever possible.



# To use optimistic locking with Spring and Hibernate, you can simply add the @Version annotation to your entity class, as described in my previous answer. Spring will automatically detect the @Version annotation and use optimistic locking for the corresponding entity.

Here's an example of using optimistic locking with Spring and Hibernate:

Add the @Version annotation to your entity class:

```java
@Entity
public class MyEntity {
    @Id
    private Long id;

    @Version
    private int version;

    // other fields and methods
}```
Create a Spring repository interface for your entity, as you would normally do. For example:

```java
public interface MyEntityRepository extends JpaRepository<MyEntity, Long> {
    // repository methods
}```
In your service or controller class, use the repository to retrieve and update the entity, as you would normally do:

```java
@Service
public class MyService {
    @Autowired
    private MyEntityRepository repository;

    @Transactional
    public void updateMyEntity(Long entityId, String someValue) {
        MyEntity entity = repository.findById(entityId).orElseThrow(EntityNotFoundException::new);
        entity.setSomeField(someValue);
        repository.save(entity);
    }
}```
If another thread/process has updated the entity since it was last read, Hibernate will throw an OptimisticLockException when you try to save the entity. You can catch this exception and handle it appropriately. For example:

```java
@Service
public class MyService {
    @Autowired
    private MyEntityRepository repository;

    @Transactional
    public void updateMyEntity(Long entityId, String someValue) {
        try {
            MyEntity entity = repository.findById(entityId).orElseThrow(EntityNotFoundException::new);
            entity.setSomeField(someValue);
            repository.save(entity);
        } catch (OptimisticLockException e) {
            // handle the exception, e.g. by retrying the operation
        }
    }
}```
That's it! Spring and Hibernate will take care of the rest, ensuring that your updates are properly versioned and protected against concurrent modifications.
