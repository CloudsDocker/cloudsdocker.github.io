---
layout: posts
title: JSON lines
---

# JSON lines


The JSON Lines format is useful because it’s stream-like, you can easily append new records to it. It doesn’t have the same problem of JSON when you run twice. Also, as each record is a separate line, you can process big files without having to fit everything in memory, there are tools like JQ to help doing that at the command-line.


# Reference
- http://jsonlines.org
- https://en.wikipedia.org/wiki/JSON_Streaming
- 
