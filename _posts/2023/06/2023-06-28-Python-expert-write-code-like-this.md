---
title: Introduction to Generator Expressions in Python
header:
    image: /assets/images/Python-expert-write-code-like-this.jpg
date: 2023-06-28
tags:
- Python
- Script
- Programming

permalink: /blogs/tech/en/Python-expert-write-code-like-this
layout: single
category: tech
---
> "It always seems impossible until it's done." - Nelson Mandela


# Filter a list of empty dictionaries in Python

Using `filter` function and lambda expression, then get first element of the list.


```python
filter_table = [d for d in table if any(d.values())]
filter_table2= list(filter(lambda d: any(d.values()), table))
row = filter_table2[0] if filter_table2 else None
```

--HTH--
