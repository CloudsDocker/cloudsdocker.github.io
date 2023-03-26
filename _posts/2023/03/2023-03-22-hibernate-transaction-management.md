To use optimistic locking with Spring and Hibernate, you can simply add the @Version annotation to your entity class, as described in my previous answer. Spring will automatically detect the @Version annotation and use optimistic locking for the corresponding entity.

Here's an example of using optimistic locking with Spring and Hibernate:

Add the @Version annotation to your entity class:
kotlin
Copy code
@Entity
public class MyEntity {
    @Id
    private Long id;

    @Version
    private int version;

    // other fields and methods
}
Create a Spring repository interface for your entity, as you would normally do. For example:
csharp
Copy code
public interface MyEntityRepository extends JpaRepository<MyEntity, Long> {
    // repository methods
}
In your service or controller class, use the repository to retrieve and update the entity, as you would normally do:
typescript
Copy code
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
}
If another thread/process has updated the entity since it was last read, Hibernate will throw an OptimisticLockException when you try to save the entity. You can catch this exception and handle it appropriately. For example:
typescript
Copy code
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
}
That's it! Spring and Hibernate will take care of the rest, ensuring that your updates are properly versioned and protected against concurrent modifications.
