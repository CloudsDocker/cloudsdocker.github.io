---
title: Compile Error Java Kotlin Coexist Project In Intellij
header:
image: /assets/images/compile-error-java-kotlin-coexist-project-in-intellij.jpg
date: 2023-04-23
tags:
- Java
- Intellij
- Coding

permalink: /blogs/tech/en/compile-error-java-kotlin-coexist-project-in-intellij
layout: single
category: tech
---

The root cause is your customized HttpMessageConverter stopped processing of WebSecurity

```java
@EnableWebMvc
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOrigins("*")
                .allowedMethods("HEAD", "GET", "PUT", "POST", "DELETE", "PATCH");
    }

    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        final Jackson2ObjectMapperBuilder builder = new Jackson2ObjectMapperBuilder()
                .indentOutput(true).dateFormat(new SimpleDateFormat("yyyy-MM-dd"));

        converters.add(new MappingJackson2HttpMessageConverter(builder.build()));
    }
}
```
