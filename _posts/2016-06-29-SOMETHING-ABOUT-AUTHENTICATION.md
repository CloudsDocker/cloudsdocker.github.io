---
layout: posts
title: Something about authentication
published: true
---
It's annoying to keep on repeating typing same login and password when you access multiple systems within office or for systems in external Internet. There are bunch of  tools / technicles to cater for such. To my best knowledge, I'll illustrate some as below.

# SSO (Single Sign On)

After you successfully log into one system,  when you hop onto other systems, so you'll no need to furhter re-enter your user name and password, and you'll in 'logged in status'. Under the scene, its sync up your login information among systems. The transferred details is typically called 'tickets'. One of the implementation logic is 'kerberos', which is one protocol developed by MIT and is widely used in such domain. In general, kerberos is supported by various systems and software, for instance, you log onto your windows desktop, your user name and password will be validated in LDAP via either client or API, you


