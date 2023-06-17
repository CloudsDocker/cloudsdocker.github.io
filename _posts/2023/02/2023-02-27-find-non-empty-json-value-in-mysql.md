---
header:
    image: /assets/images/find-non-empty-json-value-in-mysql.jpg
title:  How to find non-empty json value in mysql
date: 2023-02-23
tags:
 - DB
 - MySql
 
permalink: /blogs/tech/en/find-non-empty-json-value-in-mysql
layout: single
category: tech
---

> You are not a drop in the ocean, you are the entire ocean in a drop.

# How to find non-empty json value in mysql

To search for a non-empty JSON array in a column in MySQL, you can use the JSON_LENGTH() and JSON_EXTRACT() functions.

The JSON_LENGTH() function returns the length of a JSON array, and the JSON_EXTRACT() function extracts a value from a JSON document.

Here's an example query:

```sql
SELECT * FROM my_table WHERE JSON_LENGTH(JSON_EXTRACT(json_column, '$')) > 0;

```
This query selects all rows from the "my_table" table where the "json_column" column contains a non-empty JSON array.

In the query above, we use the JSON_EXTRACT() function to extract the entire JSON document from the "json_column" column using the '$' selector. We then use the JSON_LENGTH() function to get the length of the JSON array, and check if it's greater than zero.

You can modify the query to fit your specific table and column names, and also to search for a non-empty JSON array in a specific key within the JSON document.

--HTH--



