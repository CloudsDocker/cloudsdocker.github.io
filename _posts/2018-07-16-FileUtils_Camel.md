---
title: File Util in Apache Camel
layout: posts
---
# FileUtil.class

## compactPath(String path)
To normalize path and join with provided separator

if path is null, return null
if path.indexOf(47) == -1 && path.indexOf(92) ==-1 (means /, \) return path

### normalizePath

check whether it is windows
String osName = System.getProperty("os.name").toLowerCase(Locale.ENGLISH);
        return osName.contains("windows");
for windows, replace / with \\, for linux, replace \\ with /

split path by separator (\\ or /) to get an array

traverse array and check whether current is "..", if so , call stack.pop
otherwise, stach.push(part)

Then iterate stack and then combine them by a StringBuilder via provided addtional parameter separator

