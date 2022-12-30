---
header:
    image: /assets/images/hd_magic_micronaut_jpa.jpg
title:  Magic-in-Micronaut-JPA
date: 2022-12-30
tags:
 - Java
 - Micronaut
 
permalink: /blogs/tech/en/Magic_in_Micronaut_JPA
layout: single
category: tech
---

> The best way to predict the future is to create it.

# How findByIDAndNameOrderBy xx is resolved in Micronaut

## DataIntroductionAdvice
If you check the source of micronaunt

io/micronaut/data/intercept/DataIntroductionAdvice.java

You'll find the key logic is in findInterceptor, which will map the operation to an interceptor

```java


private @NonNull
DataInterceptor<Object, Object> findInterceptor(
@Nullable String dataSourceName,
@NonNull Class<?> operationsType,
            @NonNull Class<?> interceptorType) {
DataInterceptor interceptor;
```

The interceptor could be

 - FindOneInterceptor

 - public class DefaultFindOneInterceptor

 - public interface FindAllInterceptor<T, R> extends IterableResultInterceptor<T, R> {
- public class DefaultFindAllInterceptor<



##  DefaultFindOneInterceptor
Within following source code, 
io/micronaut/data/runtime/intercept/DefaultFindOneInterceptor.java
You may find following useful logic:

```java

@Override
public Object intercept(RepositoryMethodKey methodKey, MethodInvocationContext<T, Object> context) {
PreparedQuery<?, ?> preparedQuery = prepareQuery(methodKey, context, null);
return convertOne(
context,
operations.findOne(preparedQuery)
);
}

```

The operation is one `HibernateJpaOperations`

While in ApplicantChangesRepository

```java


@Repositorypublic interface ApplicantChangesRepository extends JpaRepository<ApplicantChange, Integer> {

```

Following method

```java
Optional<ApplicantChange> findFirstOrderByChangeIdDesc();
```

Due to cache of Hibernate, the first call to 
`applicantChangesRepository.findFirstOrderByChangeIdDesc()` will actually load ALL records into cache, 
then the 2nd call applicantChangesRepository.findFirstOrderByChangeIdDesc() 
would NO need database query.

![](/assets/images/micronaut_jpa_1.png)
![](/assets/images/micronaut_jpa_2.png)

even find first record, it still load ALL RECORDS. I think *this is one bug in Micronaunt JAP implementation*


![](/assets/images/micronaut_jpa_3.png)



--HTH--



