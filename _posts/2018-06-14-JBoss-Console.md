---
title: Jboss tips
tags:
- Jboss
- Java
layout: posts
---

# commands:

## to list all deployed applications
jboss\jboss-eap-6.4\bin\jboss-cli.bat --connect --controller=localhost:7373 --command=/deployment=*:read-attribute(name=name)

 
## to list JNDI tree:

```sh
cd /subsystem=mail
ls
/subsystem=mail/mail-session=java:jboss/mail/payment_mail


 /subsystem=naming:jndi-view()

 },
"mail" => {
    "class-name" => "javax.naming.Context",
    "children" => {
        "Default" => {
            "class-name" => "javax.mail.Session",
            "value" => "javax.mail.Session@22951e8f"
        },
        "payment_mail" => {
            "class-name" => "javax.mail.Session",
            "value" => "javax.mail.Session@548df9e2"
        }
    }
},
```
 


```xml
 <management-interfaces>
            <native-interface security-realm="ManagementRealm">
                <socket-binding native="management-native"/>
            </native-interface>
            <http-interface security-realm="ManagementRealm">
                <socket-binding http="management-http"/>
            </http-interface>
        </management-interfaces>
    </management>
xxx
<socket-binding-group name="standard-sockets" default-interface="public" port-offset="${jboss.socket.binding.port-offset:0}">
        <socket-binding name="management-native" interface="management" port="${jboss.management.native.port:7373}"/>
        <socket-binding name="management-http" interface="management" port="${jboss.management.http.port:7371}"/>
		
		
```
