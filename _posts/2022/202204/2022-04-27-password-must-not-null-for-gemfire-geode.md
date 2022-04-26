---
header:
    image: /assets/images/password_not_null_gemfire.png
title:  Password must not null in gemfire/geode, but I've assigned password in yaml properties file
date: 2022-04-27
tags:
 - springboot
 - java
 - jar
 
permalink: /blogs/tech/en/password_must_not_null_in_geode_gemfire
layout: single
category: tech
---

> Worries less, smile more!

# Summary
When you trying to bring up your service with Gemfire/geode but keep on getting following errors:
`java.security.UnrecoverableKeyException: Password must not be null`

That's very annoying because you've double or triple checked the truststore-password and keystore-password were added into application.yaml file correctly.

# Root cause

Firstly let's check the error message as below


```
Caused by: java.security.UnrecoverableKeyException: Password must not be null
	at sun.security.provider.JavaKeyStore.engineGetKey(JavaKeyStore.java:135) ~[?:?]
	at sun.security.util.KeyStoreDelegator.engineGetKey(KeyStoreDelegator.java:90) ~[?:?]
	at java.security.KeyStore.getKey(KeyStore.java:1057) ~[?:?]
	at sun.security.ssl.SunX509KeyManagerImpl.<init>(SunX509KeyManagerImpl.java:145) ~[?:?]
	at sun.security.ssl.KeyManagerFactoryImpl$SunX509.engineInit(KeyManagerFactoryImpl.java:70) ~[?:?]
	at javax.net.ssl.KeyManagerFactory.init(KeyManagerFactory.java:271) ~[?:?]
	at org.apache.geode.internal.net.SocketCreator.getKeyManagers(SocketCreator.java:407) ~[geode-core-1.13.4.jar:?]
	at org.apache.geode.internal.net.SocketCreator.createAndConfigureSSLContext(SocketCreator.java:277) ~[geode-core-1.13.4.jar:?]
	at org.apache.geode.internal.net.SocketCreator.initialize(SocketCreator.java:231) ~[geode-core-1.13.4.jar:?]
	at org.apache.geode.internal.net.SocketCreator.<init>(SocketCreator.java:196) ~[geode-core-1.13.4.jar:?]
	at org.apache.geode.internal.net.SocketCreatorFactory.createSSLSocketCreator(SocketCreatorFactory.java:113) ~[geode-core-1.13.4.jar:?]
	at org.apache.geode.internal.net.SocketCreatorFactory.getSSLSocketCreator(SocketCreatorFactory.java:87) ~[geode-core-1.13.4.jar:?]
	at org.apache.geode.internal.net.SocketCreatorFactory.getOrCreateSocketCreatorForSSLEnabledComponent(SocketCreatorFactory.java:103) ~[geode-core-1.13.4.jar:?]
	at org.apache.geode.internal.net.SocketCreatorFactory.getSocketCreatorForComponent(SocketCreatorFactory.java:73) ~[geode-core-1.13.4.jar:?]
```
If we look into details you'll find following source logic triggered this error:


```java
String passwordString = sslConfig.getKeystorePassword();
char[] password = null;
if (passwordString != null) {
    if (passwordString.trim().equals("")) {
    String encryptedPass = System.getenv("javax.net.ssl.keyStorePassword");
    if (!StringUtils.isEmpty(encryptedPass)) {
        String toDecrypt = "encrypted(" + encryptedPass + ")";
        passwordString = PasswordUtil.decrypt(toDecrypt);
        password = passwordString.toCharArray();
    }
    } else {
    password = passwordString.toCharArray();
    }
}
keyStore.load(fileInputStream, password);
// default algorithm can be changed by setting property "ssl.KeyManagerFactory.algorithm" in
// security properties
KeyManagerFactory keyManagerFactory =
    KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
keyManagerFactory.init(keyStore, password);
```

The field `password` is null lead to this error.

# Solution 

Check your configuration file , it may looks like below

```yaml
spring:
  data:
    gemfire:
      pool:
        locators: xxxxxxx
      security:
        ssl:
          components: all
          enable-endpoint-identification: true
          truststore: ${keystoreFile}
          truststore-password: 0bmr1ddH8rdw8r3
#          truststore.password: 0bmr1ddH8rdw8r3
          keystore: ${keystoreFile}
          keystore-password: 0bmr1ddH8rdw8r3
#          keystore.password: 0bmr1ddH8rdw8r3
```
> Actually the solution is to replace the hypen linked password with dot linked ones.

Tricky, right?!! 
Hope this save your time.

-HTH-

--HTH--



