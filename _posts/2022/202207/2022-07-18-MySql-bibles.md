---
header:
    image: /assets/images/hd_mysql_bible.jpg
title:  Scripts bible for MySql
date: 2022-07-18
tags:
 - MySql
 - Database
 
permalink: /blogs/tech/en/mysql_bible_scripts
layout: single
category: tech
---

> Be the Sun of your solar system.

# Summary


## Show create scripts 

```
show create table table_name;
```

## To show all records vertically (and more human-readable)
To add a postfix `\G` in each query, e.g. 

``` 
select * from table1 limit 1 \G;
```
The output will look like below, easier for developer to check and see.

![](/assets/images/mysql_verticle.jpg)




--HTH--



