---
header:
    image: /assets/images/expect-script-is-your-secret-to-productivity.jpg
title:  To increase your productivity 10 times, learn expect and read this blog
date: 2023-02-01
tags:
 - Expect
 - script
 - automation
 
permalink: /blogs/tech/en/expect-script-is-your-secret-to-productivity
layout: single
category: tech
---

> Som are born beautiful. The rest of us have to work at it.

# User scenario

It's very common in current enterprise world, your servers (such as mysql database) sit behind firewall and you have to use `jump server` to access those server.
It will be cumbersome and need lots of ceremonies to just run a single sql. Which may including following one
- find you PKI token location
- use ssh and above token connect to jump server portal
- select one appropriate environment/jump server
- sudo to server or use another ssh connect to real server
- execute command to connect to database server
- paste your real sql into command line and execute it
- copy out result and paste to your local text editor
- then you can finally get to read the data for troubleshooting/debug

oops, sooooo many ceremonies for just a single SQL run.

This is even worse if you need to do so many times a day and repeat every week, every month and every year. :-(

# Solutions
Here I'm introducing a good friend to you to save such *routine* work for you. So that you can only focus on the **core part**, that's prepare your sql and get result set of this sql.

## expect script
Expect is a scripting language that is used to automate interactive command-line processes. It is often used for automating tasks that involve logging into remote systems, executing commands on those systems, and processing the output.

Expect scripts are programs that are written in the Expect language. These scripts automate tasks by simulating user input and responding to system output. Expect scripts can be used to automate tasks such as:

Logging into remote systems and executing commands
Automating FTP or SSH file transfers
Automating Telnet sessions
Automating interactive programs such as text editors, compilers, or database tools
Monitoring and controlling system processes
Expect scripts are generally used in conjunction with other tools such as ssh, telnet, ftp, and other command line tools. Expect provides a number of built-in commands and functions that can be used to automate these tasks, such as spawn, expect, send, interact, and many others.

Overall, Expect scripts are a powerful tool for automating interactive tasks that would otherwise require manual input and monitoring. They can save time and effort and help ensure consistency and accuracy in system administration and other tasks.

## sample
Here is one sample to automate aforesaid ceremonies 

```shell

#!/usr/bin/expect -f
set timeout 120

set orderId [lindex $argv 0]
# either be orderNo or order id
set dbEnv [lindex $argv 1]
# t: test (default value if no enter) . p: production, pre: preprod
puts $dbEnv

send "Reading your login for Jumpserver from file ~/.your_own_folder/expect_username\n"
set fileUserLogin [open ~/.your_own_folder/expect_username]
gets $fileUserLogin userLogin

if {[regexp -nocase $dbEnv "t"]} {
    send "Reading database connection of test from file ~/.your_own_folder/mysql_conn_test2\n"
    set fileConnStr [open ~/.your_own_folder/mysql_conn_test2]
} elseif {[regexp -nocase $dbEnv "pre"]} {
    send "Reading database connection of preprod from file ~/.your_own_folder/mysql_conn_preprod\n"
    set fileConnStr [open ~/.your_own_folder/mysql_conn_preprod]
} elseif {[regexp -nocase $dbEnv "p"]} {
  send "Reading database connection of preprod from file ~/.your_own_folder/mysql_conn_preprod\n"
  set fileConnStr [open ~/.your_own_folder/mysql_conn_prod]
}

gets $fileConnStr conn_str

send "Start to ssh\n"
spawn ssh -i ~/dev/token/firm_token_file $userLogin@jumpserver-.your_company_name.com -p 2222
expect "JumpServer"
send "1\r"
expect "Aws-com_prod-jump-server"
send -- "3\r"
expect "https"
expect "your_company_name_develop_admin"
send "$conn_str\r"
send "select * from SalesOrder where orderNo='$orderId' or uuid='$orderId' \\G; \r"
interact

```

In short, this script will automate followings steps
- load private key token from your local disk
- spawn a new ssh terminal to connect to remote, and capture response of this session
- based on your input 1st parameter, to connect to different environments, such as test, preprod, production
- make real mysql connection to MySQL DB server behind jump server
- paste and send your SQL to execute it in Mysql Server
- capture result set and show on screen
- `interact` means it will stop there you can do further query/search


## To make expect script A to call script B

To call another expect script from within an expect script, you can use the spawn command to start a new instance of the expect interpreter and execute the other script.

Here's an example of how you can call another expect script called script2.exp from within an expect script called script1.exp:

```shell
#!/usr/bin/expect

# Start a new instance of the expect interpreter and execute script2.exp
spawn expect script2.exp

# Wait for the other script to finish executing
expect eof
```

In the above example, the spawn command starts a new instance of the expect interpreter and executes the script2.exp script. The expect eof command waits for the other script to finish executing before exiting the current script.

Note that you can also pass command line arguments to the other expect script using the spawn command. For example, to pass the arguments arg1 and arg2 to script2.exp, you can modify the spawn command as follows:

```shell
spawn expect script2.exp arg1 arg2
```
This will start the script2.exp script with the arguments arg1 and arg2.


--HTH--



