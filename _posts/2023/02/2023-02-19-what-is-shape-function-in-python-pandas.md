---
header:
    image: /assets/images/what-is-shape-function-in-python-pandas-2.jpg
title:  What is shape function in python pandas
date: 2023-02-19
tags:
 - Python
 - Pandas
 - DataScience
 
permalink: /blogs/tech/en/what-is-shape-function-in-python-pandas
layout: single
category: tech
---

> Imagination is the key ingredient to a happy life.

# what is shape function in python pandas

In the Python Pandas library, the shape function is used to get the dimensions of a DataFrame or a Series. It returns a tuple containing the number of rows and columns of the DataFrame or Series.

The shape function can be called on a Pandas DataFrame or Series object as follows:

```python
import pandas as pd

# create a sample DataFrame
df = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})

# get the shape of the DataFrame
shape = df.shape

# print the shape
print(shape) # output: (3, 2)
```

In the example above, the shape function is called on a Pandas DataFrame object df, which contains 3 rows and 2 columns. The shape function returns a tuple containing the number of rows (3) and columns (2).

The shape function is useful for getting an overview of the dimensions of a DataFrame or Series and for performing calculations or operations that depend on the size of the data.

--HTH--



