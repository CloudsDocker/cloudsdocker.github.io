---
title: Mysql Operator To Extract Json
header:
    image: /assets/images/mysql_operator_to_extract_JSON.jpg
date: 2023-03-16
tags:
 - mysql
 - database

permalink: /blogs/tech/en/mysql_operator_to_extract_JSON
layout: single
category: tech
---
> "Believe you can and you're halfway there." - Theodore Roosevelt

# Mysql operator to extract JSON

In MySQL, the "->>" operator is used to extract a specific value from a JSON object. It is also known as the JSON extract operator.

The operator is used to retrieve the value of a specific key from a JSON object. The "->>" operator returns the value as a string.

For example, consider a JSON object named "person" with the following structure:

```json
{
    "name": "John",
    "age": 30,
    "address": {
        "city": "New York",
        "state": "NY",
        "zip": "10001"
    }
}
```
To extract the value of the "city" key from the "address" object using the "->>" operator, the following SQL statement can be used:


```sql
SELECT person->>'$.address.city' as city FROM table_name;
```
This will return the value "New York" as a string. The "$." symbol is used to indicate the root of the JSON object and the "->>" operator is used to extract the value of the "city" key.



--End--
