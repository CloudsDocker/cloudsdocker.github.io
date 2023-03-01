---
header:
    image: /assets/images/yarn_npm_install.jpg
title:  ow to extract table name from SQL by python
date: 2023-03-01
tags:
 - Python
 - AI
 - Automation
 
permalink: /blogs/tech/en/extract-table-name-from-SQL-by-python
layout: single
category: tech
---

> You are not a drop in the ocean, you are the entire ocean in a drop.

# How to extract table name from SQL by python

To extract the table name from an SQL INSERT INTO statement using Python regular expressions, you can use the re module. Here is an example code snippet that demonstrates how to do this:

```python

import re

insert_statement = "INSERT INTO my_table (column1, column2, column3) VALUES ('value1', 'value2', 'value3')"

# Define the regular expression pattern
pattern = r"^INSERT\s+INTO\s+(\w+)\s*"

# Use the re.search() function to find the table name
match = re.search(pattern, insert_statement)

# Extract the table name from the matched string
if match:
table_name = match.group(1)

print(table_name)  # prints 'my_table'

```

In the code above, we define a regular expression pattern that matches the INSERT INTO keyword, followed by one or more whitespace characters (\s+), followed by the table name, which we capture using a group (\w+). The \w+ pattern matches one or more word characters (letters, digits, and underscores). The ^ at the beginning of the pattern ensures that we only match the beginning of the string.

We then use the re.search() function to find the first occurrence of the pattern in the insert_statement string. If a match is found, we extract the table name from the first capturing group (match.group(1)) and print it out.

Note that this is a simple example and may not work for all SQL INSERT INTO statements. For example, if the statement includes a schema name, or if the table name is enclosed in quotes or backticks, the regular expression will need to be adjusted accordingly.




Regenerate response


--HTH--



