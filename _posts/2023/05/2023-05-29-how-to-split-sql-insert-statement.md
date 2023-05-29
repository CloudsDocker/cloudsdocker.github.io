---
title: How To Split Sql Insert Statement
header:
    image: /assets/images/how-to-split-sql-insert-statement.jpg
date: 2023-05-29
tags:
- Regular Expression
- Programming
- AI

permalink: /blogs/tech/en/how-to-split-sql-insert-statement
layout: single
category: tech
---
> "Don't let yesterday take up too much of today." - Will Rogers

# Case study
Assume you have a SQL INSERT statement like this:

```sql
INSERT INTO table_name VALUES (value1, value2, value3, ...);
```
If you want to split the values into a list, you can use the following code snippet:

```python
import re
split_values = values.split(",")
```
If work in some case until for some values contains comma (,) inside single quotes ('), like this:

```sql
INSERT INTO table_name VALUES (value1, value2, 'value3, value3.1', ...);
```
In this case, the split() method will not work as expected. To handle this case, you can use the following code snippet:

```python
split_values = re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", values)
```

# Elaboration

Let's break down the code snippet `re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", values)`:

The re.split() function is used to split a string based on a specified pattern. 
In this case, the pattern is `",(?=(?:[^']*'[^']*')*[^']*$)"`.

Now, let's analyze the pattern:

 - , - This matches a comma (,) character, which serves as the delimiter for splitting the string.

 - (?=(?:[^']*'[^']*')*[^']*$) - This is a positive lookahead assertion. It ensures that the comma (,) is followed by a specific pattern without actually consuming it during the split.

 - (?:[^']*'[^']*')* - This non-capturing group (?: ... ) matches zero or more occurrences of the following pattern: any character except a single quote ([^']*), followed by a single quote ('), followed by any character except a single quote ([^']*), and another single quote ('). Essentially, it matches pairs of single quotes and any characters between them.

 - [^']*$ - This matches any character except a single quote ([^']*) until the end of the string ($). It ensures that there are no unmatched single quotes after the comma.

Therefore, the overall pattern `",(?=(?:[^']*'[^']*')*[^']*$)"` matches a comma (,) only if it is followed by an even number of single quotes (indicating it is not inside a pair of quotes).

The re.split() function splits the values string based on this pattern, effectively separating the values for each column while ignoring commas inside quotes. The resulting list, split_values, contains the extracted values.

Note that the strip("'") method is applied to each value in the for loop to remove the surrounding single quotes.

---


--HTH--
