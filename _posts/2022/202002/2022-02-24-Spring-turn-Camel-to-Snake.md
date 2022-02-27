---
header:
    image: /assets/images/hd_jpa_col.png
title:  Why Spring turn a column name from camelNaming to snake_Naming
date: 2022-02-24
tags:
 - SpringBoot
 - Java
 - SpringData
 - JPA
 
permalink: /blogs/tech/en/camel_to_snake_in_jpa
layout: single
category: tech
---

> Don't spend another year doing the same shit.


# Why Spring turn a column name from camelNaming to snake_Naming?


## Symptoms:


There is one 'column name xx is not valid' in SQLServerException, below is one sample console output

```bash
by: com.microsoft.sqlserver.jdbc.SQLServerException: The column name v_book is not valid.
at com.microsoft.sqlserver.jdbc.SQLServerException.makeFromDriverError(SQLServerException.java:234)
at com.microsoft.sqlserver.jdbc.SQLServerResultSet.findColumn(SQLServerResultSet.java:699)
at com.microsoft.sqlserver.jdbc.SQLServerResultSet.getString(SQLServerResultSet.java:2525)
at com.zaxxer.hikari.pool.HikariProxyResultSet.getString(HikariProxyResultSet.java)
at org.hibernate.type.descriptor.sql.VarcharTypeDescriptor$2.doExtract(VarcharTypeDescriptor.java:62)
at org.hibernate.type.descriptor.sql.BasicExtractor.extract(BasicExtractor.java:47)
at org.hibernate.type.AbstractStandardBasicType.nullSafeGet(AbstractStandardBasicType.java:257)
at org.hibernate.type.AbstractStandardBasicType.nullSafeGet(AbstractStandardBasicType.java:253)
at org.hibernate.type.AbstractStandardBasicType.nullSafeGet(AbstractStandardBasicType.java:243)
at org.hibernate.type.AbstractStandardBasicType.hydrate(AbstractStandardBasicType.java:329)
```



## SpringData explained & Troubleshooting:


In short answer, this is caused by default `NamingStrategy` implementation , which is SpringPhysicalNamingStrategy assigned by SpringBoot Data . Which is trying to smartly guess and set it up as default naming strategy provider.


Under the hood, it's implementation (listed as below)

```java
@Override
  public Identifier toPhysicalColumnName(Identifier name, JdbcEnvironment jdbcEnvironment) {
        return apply(name, jdbcEnvironment);
 }
....
private boolean isUnderscoreRequired(char before, char current, char after) {
        return Character.isLowerCase(before) && Character.isUpperCase(current) && Character.isLowerCase(after);
    }
```

It will change `camelNaming` to `snake_naming`, for example, `myColumn`  will be translated to `my_Column`  , which is align with Spring's naming convention.



As below sample column transformation: vCriteria will be changed to `v_Criteria`

![](\../../../assets/images/jpa_camel_snake.png)



Here's the code logic FYI.

![](\../../../assets/images/camel_snake_logic.png)



## Solution

There are few solutions for the fix

### Disable NamingStrategy 
 Firstly and quickest one: remove annotation of @Column, this is actually the marker annotation to trigger Spring's naming strategy logic. 


### Chose another NamingStrategy 
If you still need annotation @Column (e.g. for calculation or columnDefinition), you can explicitly change its naming strategy, such as below sample:

```yaml
spring:
  jpa:
    hibernate:
      naming:
        physical-strategy: org.hibernate.boot.model.naming.PhysicalNamingStrategyStandardImpl
```

> This PhysicalNamingStrategyStandardImpl  is one of two implementations of Hibernate's PhysicalNamingStrategy interface. It's logic is straightforward, purely return whatever the name it get from database.

--END--




