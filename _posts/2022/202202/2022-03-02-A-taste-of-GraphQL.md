---
header:
    image: /assets/images/hd_jpa_springdata.png
title:  A taste of GraphQL
date: 2022-03-02
tags:
 - GraphQL
 - Java
 - SpringData
 
permalink: /blogs/tech/en/build_own_spring_annotation
layout: single
category: tech
---

> A good day starts with a good mindset!


# Introduction

Firstly let's talk why and Benefits of GraphQL
Some of them are:

a. No Over-fetching and Under-fetching of Data — Subscribe for what you want

b. Reduces Network Latency

c. Supports Dynamic API Responses

d. Single Endpoint

e. Reducing the concept of Versioning the APIs

f. No more Strict Handshake between developers — De Coupling

## Taste of source code

```JavaScript
{
    query{
        user{
            game
            age
        }
    }
}

```

## Operation type
`query` is one operation, alternatively options are `mutation` and `subscription`

### Query 
This type will translated to RESTFul `GET`

### Mutation
This type will translated to RESTFul `POST`, `PUT`, `PATCH` or `DELETE`

### Subscription
This type will translated to a realtime connection via `WebSockets`



## Operation "endpoint"
`user` is for one endpoint

## Requested fields
`game` and `age` are fields expected to returning.

# Technical details

# post
Please be advised GraphQL only support `POST` even for some `get` operations.


## endpoint

`/graphql` is the built-in interface

This will auto discover following modules

 . Type definition
 . Query Definition
 . Mutation definition
 . Subscription definition

All of above modules will routed to `Resolvers` and your server side logic

# One real world example

## schema file
Firstly create one graphql schema file `books.graphql`

```JavasScrip

schema {
    query: Query
}

type Book {
    isin: String
    title: String
    publisher: String
    authors: [String]
    publishDate: String
}

type Query{
    allBooks: [Books]
    book(id: String): Book
}


```

Here are Java code

```java
//Get the schema source
        final val resourceFile = resource.getFile();
        
        // parse the schema
        TypeDefinitionRegistry typeDefinitionRegistry= new SchemaParser().parse(resourceFile);
        RuntimeWiring wiring= buildRuntimeWiring();
        final val qlSchema = new SchemaGenerator().makeExecutableSchema(typeDefinitionRegistry, wiring);
        final val graphQL = GraphQL.newGraphQL(qlSchema).build();
        log.info("build graphQL on resource config:{}", resourceFile);
```
1. Load resource via import org.springframework.core.io.Resource;
2. Build a `TypeDefinitionRegistry` to bind you defined *type* , e.g. **Book**
3. RuntimeWiring is used to wire type and query in GraphQL
4. `SchemaGenerator().makeExecutableSchema` will make the schema executable so that we can use it in our code.
5. To boot strap a new GraphQL via `GraphQL.newGraphQL(qlSchema).build`




--END--




