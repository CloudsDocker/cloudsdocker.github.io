---
header:
    image: /assets/images/hd_jpa_springdata.png
title:  What's inside magic in Spring Data JPA
date: 2022-02-25
tags:
 - SpringBoot
 - Java
 - SpringData
 
permalink: /blogs/tech/en/secrets_in_springdata_jpa
layout: single
category: tech
---

> A good day starts with a good mindset!


# How does Spring-Data JPA work to bootstrap Hibernate ?

## Highlevel diagram

Here is the diagram for high level overview of JPA strucutre.
![](\../../../assets/images/jpa_spring_data.png)


## Details explained

Generally if you included spring-boot-starter-data-jpa   in your maven file, several default configuration will be loaded by conventions. LIsted as below:

 1. One bean named **entityManagerFactory**  will be loaded. By default, spring ORM framework provided one default implementation : `org.springframework.orm.jpa.AbstractEntityManagerFactoryBean`
 1. Similar to most SpringBoot functionalities (such as JDBC, AppServer etc.), it will scan current class path to find one suitable **provider** via `SPI (Service Provider Interface)` . Each provider (if you want to implement your own provider), should implement interface *PersistenceProvider*. Essentially the implementation should implementation method `createEntityManagerFactory` to create new **EntityManagerFactory**.
 1. SpringBoot provided the default implementation: `SpringHibernateJpaPersistenceProvider` ( at *\org\springframework\orm\jpa\vendor\SpringHibernateJpaPersistenceProvider.java*)
 1. This would build a new `EntityManagerFactoryBuilderImpl` instance, which is one Hibernate class (under  *org\hibernate\jpa\boot\internal\EntityManagerFactoryBuilderImpl.java*) , it build a new EntityManagerFactory.
 1. Internally it will invoke `SessionFactoryBuilder.build`,  which will create a new instance of `SessionFactory`. Usually an application has a single SessionFactory instance and threads servicing client requests obtain Session instances from this factory.
 1. Then developers can chose to call `SessionFactory.openSession` to get a new Session object. This is the main runtime interface between a Java application and Hibernate. This is the central API class abstracting the notion of a persistence service.  The lifecycle of a Session is bounded by the beginning and end of a logical transaction. (Long transactions might span several database transactions.)  The main function of the Session is to offer create, read and delete operations for instances of mapped entity classes. 
 1. A typical transaction should use the following idiom:  


```java
Session sess = sessionFactory.openSession();
 Transaction tx;
 try {
     tx = sess.beginTransaction();
     //do some work
     ...
     tx.commit();
 }
 catch (Exception e) {
     if (tx!=null) tx.rollback();
     throw e;
 }
 finally {
     sess.close();
 }
 ```
--END--




