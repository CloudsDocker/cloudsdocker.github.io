---
title: Whitelabel Error Page
date: 2021-09-13
tags:
 - Financial
 - Debts
toc: true
header:
    image: /assets/images/hd_header.jpg
---

# Summary
Whitelabel Error Page is the default error page in Spring Boot web app.
It provide a more user-friently error page whenever there are any issues when user trying to access a apge.

![](/assets/images/WhileLabelErrorPage.png)

Generally this is good to end users but we may watnt to see more error details during `develop/debug` stage. To show error stack trace, you can add following annotation in front of your `SpringApplicaiton` main class.

```java
@SpringBootApplication(exclude = {ErrorMvcAutoConfiguration.class})
public class YourWebApplication {
```

After this change and restart your application, you'd see your familiar error page. :-)

![](/assets/images/WhiteLabelError_Normal.png)


--End--
