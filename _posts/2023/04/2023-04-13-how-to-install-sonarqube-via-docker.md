---
title: how-to-auto-login-for-citrix-receiver-vpn-client
header:
    image: /assets/images/how-to-install-sonarqube-via-docker.jpg
date: 2023-04-13
tags:
- vpn
- citrix
- AI automation

permalink: /blogs/tech/en/how-to-auto-login-for-citrix-receiver-vpn-client
layout: single
category: tech
---

> "Hang Out with People Who are Better than You." — Warren Buffett

# Automate Citrix Secure Access Login with PowerShell

Open Notepad or any other text editor.

Type the following command:

```shell
$wshell = New-Object -ComObject wscript.shell
$wshell.AppActivate('Citrix Secure Access Login')
Sleep 1
$wshell.SendKeys('username')
Sleep 1
$wshell.SendKeys('{TAB}')
Sleep 1
$wshell.SendKeys('password')
Sleep 1
$wshell.SendKeys('{TAB}')
Sleep 1
$wshell.SendKeys('{ENTER}')
```

Replace 'username' and 'password' with your actual Citrix Secure Access login credentials.

Save the file with a .ps1 extension. For example, CitrixLogin.ps1.

Open Task Scheduler by typing "Task Scheduler" in the Windows search bar and selecting the app.

Click on "Create Task" in the "Actions" menu on the right-hand side.

Name your task and select the appropriate user account.

Under the "Triggers" tab, click on "New" to create a new trigger.

Select the appropriate trigger option for your needs. For example, you may want the task to run each time you log in.

Under the "Actions" tab, click on "New" to create a new action.

Select "Start a program" as the action type.

In the "Program/script" field, enter "powershell.exe".

In the "Add arguments" field, enter the location of your script file. For example, "C:\Users\YourUsername\Desktop\CitrixLogin.ps1".

Click on "OK" to save your action and then "OK" again to save your task.

Test your task by logging out and then logging back in to Windows 10. The task should automatically enter your Citrix Secure Access login credentials.

Please note that automating the entry of your Citrix Secure Access login credentials can pose a security risk, so use this method with caution and only if necessary.


--HTH--
