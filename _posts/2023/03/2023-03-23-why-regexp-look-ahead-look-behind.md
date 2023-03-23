---
title: A Brief Introduction to Lookbehind and Lookahead in Regular Expressions
header:
    image: /assets/images/why-regexp-look-ahead-look-behind.jpg
date: 2023-03-20
tags:
 - RegularExpression
 - Regexp
 - Python

permalink: /blogs/tech/en/why-regexp-look-ahead-look-behind
layout: single
category: tech
---
> "The only way to do great work is to love what you do." - Steve Jobs

# A Brief Introduction to Lookbehind and Lookahead in Regular Expressions

## Introduction:

Regular expressions are a powerful tool for searching, matching, and manipulating text. Two advanced features that can make your regex patterns even more efficient and flexible are lookbehind and lookahead. These are zero-width assertions that don't consume any characters in the input string but help to match patterns based on the context around the current position. In this blog post, we'll provide a brief overview of lookbehind and lookahead, their syntax, and some examples to demonstrate their usage.

### Lookbehind:

Lookbehind allows you to check if the text before the current position matches a certain pattern without including the matched text in the result. In regular expressions, lookbehind is denoted by (?<=...), where the ... represents the pattern you want to look for before the current position.

#### Example:

Suppose you want to match a monetary value without the currency symbol (e.g., "123.45" in "$123.45"). You can use lookbehind as follows:

```shell
(?<=\$)\d+(\.\d{2})?
```

The lookbehind (?<=\$) checks if the current position is preceded by a dollar sign $, but it doesn't include the dollar sign in the match.

### Lookahead:

Lookahead allows you to check if the text after the current position matches a certain pattern without including the matched text in the result. In regular expressions, lookahead is denoted by (?=...), where the ... represents the pattern you want to look for after the current position.

#### Example:

Suppose you want to match a number that is immediately followed by the string "px" (e.g., "16" in "16px"). You can use lookahead as follows:

```shell
\d+(?=px)
```

The lookahead (?=px) checks if the current position is followed by the string "px", but it doesn't include the "px" in the match.

### Conclusion:

Lookbehind and lookahead are powerful features in regular expressions that allow you to match patterns based on their surrounding context without including that context in the match itself. By understanding and utilizing these assertions, you can create more flexible and efficient regex patterns to match and manipulate text in your applications.


# Deep Dive for lookbehind and lookahead

## what is lookbehind
Lookbehind is a feature in regular expressions that allows you to check if the text before the current position matches a certain pattern, without actually including the matched text in the result. It's a kind of assertion that doesn't consume any characters in the input string, but only checks if a subpattern matches at the current position.

In regular expressions, lookbehind is denoted by (?<=...), where the ... represents the pattern you want to look for before the current position.

For example, consider the following regular expression pattern:

```python

(?<=\$)\d+(\.\d{2})?
```

This pattern matches a monetary value without the currency symbol (e.g., "123.45" in "$123.45"). The lookbehind (?<=\$) checks if the current position is preceded by a dollar sign $, but it doesn't include the dollar sign in the match.

Here's a Python example demonstrating the use of lookbehind:

```python

import re

text = "The price is $123.45 for the product."
pattern = r'(?<=\$)\d+(\.\d{2})?'

match = re.search(pattern, text)

if match:
    print(match.group())
else:
    print("No match found")
```

This code snippet will output "123.45" as it matches the monetary value without the dollar sign, thanks to the lookbehind assertion.


## what's is lookahead
Lookahead is a feature in regular expressions that allows you to check if the text after the current position matches a certain pattern, without actually including the matched text in the result. It's a kind of assertion that doesn't consume any characters in the input string but only checks if a subpattern matches at the current position.

In regular expressions, lookahead is denoted by (?=...), where the ... represents the pattern you want to look for after the current position.

For example, consider the following regular expression pattern:

```python
\d+(?=px)
```
This pattern matches a number that is immediately followed by the string "px" (e.g., "16" in "16px"). The lookahead (?=px) checks if the current position is followed by the string "px", but it doesn't include the "px" in the match.

Here's a Python example demonstrating the use of lookahead:

```python
import re

text = "The font size is 16px."
pattern = r'\d+(?=px)'

match = re.search(pattern, text)

if match:
    print(match.group())
else:
    print("No match found")
```

This code snippet will output "16" as it matches the number immediately followed by the "px" string, thanks to the lookahead assertion.

--End--
