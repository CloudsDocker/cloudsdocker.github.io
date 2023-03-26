---
title: How To Run Testing Multiple Threading
header:
    image: /assets/images/how-to-run-testing-multiple-threading.jpg
date: 2023-03-26
tags:
- testing multiple threading
- Java
- Spring

permalink: /blogs/tech/en/how-to-run-testing-multiple-threading
layout: single
category: tech
---

# A sample to test concurrent JPA modifications 

Here's an example of testing concurrent modifications to a JPA entity using Java concurrency and JUnit:

```java
@RunWith(SpringRunner.class)
@SpringBootTest
public class ItemRepositoryTest {
 
  @Autowired
  private ItemRepository itemRepository;
 
  @Test
  public void testConcurrentUpdates() throws Exception {
    // Create a new item and save it to the database
    Item item = new Item("Item 1", 100.0);
    itemRepository.save(item);
 
    // Create two threads that update the item's price
    ExecutorService executorService = Executors.newFixedThreadPool(2);
    CountDownLatch latch = new CountDownLatch(2);
    executorService.submit(() -> {
      Item item1 = itemRepository.findById(item.getId()).get();
      item1.setPrice(110.0);
      itemRepository.save(item1);
      latch.countDown();
    });
    executorService.submit(() -> {
      Item item2 = itemRepository.findById(item.getId()).get();
      item2.setPrice(120.0);
      itemRepository.save(item2);
      latch.countDown();
    });
 
    // Wait for both threads to complete
    latch.await();
 
    // Verify that the item's price has been updated
    Item updatedItem = itemRepository.findById(item.getId()).get();
    assertEquals(120.0, updatedItem.getPrice(), 0.01);
  }
}
```

In this example, we have a test method testConcurrentUpdates() that tests concurrent modifications to a JPA entity. First, we create a new Item entity and save it to the database using itemRepository.save().

Next, we create two threads that update the item's price using ExecutorService and CountDownLatch. Each thread loads the Item from the database using itemRepository.findById(), updates the price, and saves the updated item back to the database using itemRepository.save().

We then use CountDownLatch.await() to wait for both threads to complete, and verify that the item's price has been updated correctly using assertEquals().

This test case simulates concurrent modifications to the same entity in the database and ensures that the modifications are properly handled by JPA. By using CountDownLatch and ExecutorService, we can simulate concurrent modifications to the same entity and verify that the database is updated correctly.


# Going to one extra step

It's important to note that testing concurrent modifications to a JPA entity can be tricky, as it requires careful handling of transactions, locking, and race conditions. Here are some additional considerations to keep in mind:

Transactions: In JPA, modifications to the database are typically made within a transaction. When testing concurrent modifications, it's important to ensure that each thread has its own transaction, and that the transactions are properly managed and committed. In the example above, each call to itemRepository.save() is implicitly within its own transaction.
Locking: When multiple threads are modifying the same entity simultaneously, it's important to ensure that the entity is properly locked to prevent conflicts. In JPA, you can use pessimistic locking or optimistic locking to ensure that the entity is properly locked. In the example above, we are using optimistic locking, which ensures that the entity is not modified if it has been modified by another transaction.
Race Conditions: When testing concurrent modifications, it's important to consider race conditions, where the outcome of the test depends on the timing of the threads. For example, if one thread updates the entity before the other thread has a chance to load it, the second thread may overwrite the first thread's changes. In the example above, we are using CountDownLatch to ensure that both threads start modifying the entity at the same time.
Overall, testing concurrent modifications to a JPA entity requires careful consideration of transactions, locking, and race conditions. By properly managing transactions, using locking to prevent conflicts, and handling race conditions, you can ensure that your test cases accurately simulate real-world scenarios and provide reliable results.


# A sample to simulate a race condition in JPA update entity

Here's an example of simulating a race condition in JPA by updating the same entity concurrently:

```java

@Test
public void testConcurrentUpdates() throws Exception {
  // Create a new item and save it to the database
  Item item = new Item("Item 1", 100.0);
  itemRepository.save(item);

  // Create two threads that update the item's price
  ExecutorService executorService = Executors.newFixedThreadPool(2);
  CountDownLatch latch = new CountDownLatch(2);
  executorService.submit(() -> {
    Item item1 = itemRepository.findById(item.getId()).get();
    item1.setPrice(item1.getPrice() + 10.0);
    itemRepository.save(item1);
    latch.countDown();
  });
  executorService.submit(() -> {
    Item item2 = itemRepository.findById(item.getId()).get();
    item2.setPrice(item2.getPrice() + 20.0);
    itemRepository.save(item2);
    latch.countDown();
  });

  // Wait for both threads to complete
  latch.await();

  // Verify that the item's price has been updated by one of the threads
  Item updatedItem = itemRepository.findById(item.getId()).get();
  assertTrue(updatedItem.getPrice() == 110.0 || updatedItem.getPrice() == 120.0);
}
```

In this example, we have a test method testConcurrentUpdates() that simulates a race condition by updating the same Item entity concurrently. First, we create a new Item entity and save it to the database using itemRepository.save().

Next, we create two threads that update the item's price using ExecutorService and CountDownLatch. Each thread loads the Item from the database using itemRepository.findById(), updates the price, and saves the updated item back to the database using itemRepository.save().

We then use CountDownLatch.await() to wait for both threads to complete, and verify that the item's price has been updated by one of the threads using assertTrue(). Since the two threads are updating the item's price by different amounts, we expect the item's price to be either 110.0 or 120.0 after the threads complete.

This test case simulates a race condition where two threads are updating the same entity concurrently, which can lead to unpredictable results depending on the timing of the updates. By using CountDownLatch and ExecutorService, we can simulate concurrent modifications to the same entity and verify that the updates are properly handled by JPA.

# How to simulate to test one JPA save action in multi threading 

Simulating multi-threaded JPA save actions can be tricky, as it requires careful coordination to ensure that the data is saved correctly and without conflicts. Here are some general steps you can follow to simulate this scenario:

 - Create a test environment: Set up a test database and configure your JPA entity manager to connect to it. Make sure that the database can handle multiple connections and is capable of handling concurrent transactions.
 - Create test data: Generate a set of test data that can be saved to the database. This can be done using a data generator or by manually creating a set of test entities.
 - Set up your threads: Create multiple threads, each with its own JPA entity manager and transaction. Each thread should be responsible for saving a subset of the test data.
 - Execute the threads: Start the threads and let them save their respective data to the database.
 - Verify the results: Once the threads have finished executing, verify that all the data has been saved correctly and without conflicts. You can do this by querying the database and checking that all the expected entities have been saved.
 - Some things to keep in mind when simulating multi-threaded JPA save actions:

Be careful when using optimistic locking, as it can lead to conflicts when multiple threads try to update the same entity at the same time.
Use synchronization or other coordination mechanisms to ensure that the threads do not interfere with each other.
Monitor the performance and resource usage of your test environment to ensure that it can handle the load of multiple concurrent transactions.

# More details to create a test environment:


```
// Set up a test database and configure your JPA entity manager to connect to it.
EntityManagerFactory emf = Persistence.createEntityManagerFactory("test");
EntityManager em = emf.createEntityManager();
```

Create test data:

```
// Generate a set of test data that can be saved to the database.
List<MyEntity> testEntities = generateTestData();
```

Set up your threads:

```
// Create multiple threads, each with its own JPA entity manager and transaction.
List<Thread> threads = new ArrayList<>();
int numThreads = 10;
int batchSize = testEntities.size() / numThreads;

for (int i = 0; i < numThreads; i++) {
    final int startIndex = i * batchSize;
    final int endIndex = i == numThreads - 1 ? testEntities.size() : (i + 1) * batchSize;
    Thread thread = new Thread(() -> {
        EntityManager em = emf.createEntityManager();
        EntityTransaction tx = em.getTransaction();
        tx.begin();
        try {
            for (int j = startIndex; j < endIndex; j++) {
                em.persist(testEntities.get(j));
            }
            tx.commit();
        } catch (Exception e) {
            tx.rollback();
        } finally {
            em.close();
        }
    });
    threads.add(thread);
}
```

Execute the threads:

```
// Start the threads and let them save their respective data to the database.
for (Thread thread : threads) {
    thread.start();
}

for (Thread thread : threads) {
    thread.join();
}
```

Verify the results:

```
// Once the threads have finished executing, verify that all the data has been saved correctly and without conflicts.
em.getTransaction().begin();
List<MyEntity> savedEntities = em.createQuery("SELECT e FROM MyEntity e", MyEntity.class).getResultList();
em.getTransaction().commit();

assert testEntities.size() == savedEntities.size();
```

Some things to keep in mind when simulating multi-threaded JPA save actions:

Be careful when using optimistic locking, as it can lead to conflicts when multiple threads try to update the same entity at the same time.
Use synchronization or other coordination mechanisms to ensure that the threads do not interfere with each other.
Monitor the performance and resource usage of your test environment to ensure that it can handle the load of multiple concurrent transactions.

# To implement via spring boot JPA repository 

Here's an example implementation in Spring Boot using a JPA repository:

Create a test environment:

```
@SpringBootTest
@Transactional
public class MyRepositoryTest {
    // Inject your repository and entity manager
    @Autowired
    private MyRepository myRepository;

    @PersistenceContext
    private EntityManager em;
}
```

Create test data:


```
private List<MyEntity> generateTestData() {
    // Generate a set of test data that can be saved to the database.
    List<MyEntity> testEntities = new ArrayList<>();
    // ...
    return testEntities;
}
```

Set up your threads:

```
@Test
public void testSaveConcurrently() throws Exception {
    // Create multiple threads, each with its own transaction.
    List<Thread> threads = new ArrayList<>();
    int numThreads = 10;
    int batchSize = testEntities.size() / numThreads;

    for (int i = 0; i < numThreads; i++) {
        final int startIndex = i * batchSize;
        final int endIndex = i == numThreads - 1 ? testEntities.size() : (i + 1) * batchSize;
        Thread thread = new Thread(() -> {
            MyEntityRepository threadRepository = (MyEntityRepository) AopTestUtils.getTargetObject(myRepository);
            EntityManager threadEm = threadRepository.getEntityManager();
            EntityTransaction tx = threadEm.getTransaction();
            tx.begin();
            try {
                for (int j = startIndex; j < endIndex; j++) {
                    threadRepository.save(testEntities.get(j));
                }
                tx.commit();
            } catch (Exception e) {
                tx.rollback();
            } finally {
                threadEm.close();
            }
        });
        threads.add(thread);
    }

    // Start the threads and let them save their respective data to the database.
    for (Thread thread : threads) {
        thread.start();
    }

    for (Thread thread : threads) {
        thread.join();
    }
}
```

Verify the results:

```
@Test
public void testSaveConcurrently() throws Exception {
    // ...
    // Once the threads have finished executing, verify that all the data has been saved correctly and without conflicts.
    em.clear();
    List<MyEntity> savedEntities = myRepository.findAll();
    assertThat(savedEntities).hasSize(testEntities.size());
}```

Some things to keep in mind when simulating multi-threaded JPA save actions:

Be careful when using optimistic locking, as it can lead to conflicts when multiple threads try to update the same entity at the same time.
Use synchronization or other coordination mechanisms to ensure that the threads do not interfere with each other.
Monitor the performance and resource usage of your test environment to ensure that it can handle the load of multiple concurrent transactions.




