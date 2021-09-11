---
title: How to decode path parameters in All REST WebServices calls
date: 2020-08-03
tags:
 - RESTful
 - WebServices
layout: posts
---
# How to decode path parameters in All REST WebServices calls

> TL:DR
> If there are multiple places requires decode a parameter during WebServices RESTful calls, you can use UrlPathHelper from springframework to do this in central place

Image there is one `param1` in RESTful URL which may contains some **Non URL friendly** characters, such as forward slash "/". You definitely can call `URLCodec().decode(param1)` on every calls. But that's cumbersome and error-prone.

Thanks to springframework's support of URL intercepor, you can extend UrlPathHelper and overwrite decodePathVariables to do this in one central place.

Below is one `kotlin` and `java` samples just FYI:

## Kotlin

```kotlin
import org.apache.commons.codec.net.URLCodec
import org.springframework.web.util.UrlPathHelper
import javax.servlet.http.HttpServletRequest

class MyPathHelper : UrlPathHelper() {
    override fun decodePathVariables(request: HttpServletRequest, vars: MutableMap<String, String>): MutableMap<String, String> {
        val map = super.decodePathVariables(request, vars)
        map.computeIfPresent("param1") { _, v -> URLCodec().decode(v) }
        return map
    }
}
```
## Java

```java
import org.apache.commons.codec.DecoderException;
import org.apache.commons.codec.net.URLCodec;
import org.springframework.web.util.UrlPathHelper;

import java.util.Map;

public class  MyPathHelper extends UrlPathHelper {
    @Override
    public Map<String, String> decodePathVariables(javax.servlet.http.HttpServletRequest request, Map<String, String> vars) {
        Map<String, String> map = super.decodePathVariables(request, vars);
        map.computeIfPresent("param1", (k,v) -> {
            try {
                return new URLCodec().decode(v);
            } catch (DecoderException e) {
                e.printStackTrace();
            }
            return v;
        });
        return map;
    }
}
```


Hope this help!

--End--
