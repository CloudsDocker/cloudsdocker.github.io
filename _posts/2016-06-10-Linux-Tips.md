---
layout: posts
title: Linux Tips
tags:
 - Linux
 - DevOps
---
# Get permission denied error when sudo su (or hyphen in sudo command)
bash: /home/YOURNAME/.bashrc: Permission denied
That's because you didn't add "-" hyphen in your sudo command.

The difference between "-" and "no hyphen" is that the latter keeps your existing environment (variables, etc); the former creates a new environment (with the settings of the actual user, not your own).

The hyphen has two effects:

1) switches from the current directory to the home directory of the new user (e.g., to /root in the case of the root user) by logging in as that user

2) changes the environmental variables to those of the new user as dictated by their ~/.bashrc. That is, if the first argument to su is a hyphen, the current directory and environment will be changed to what would be expected if the new user had actually logged on to a new session (rather than just taking over an existing session).

# To delete lines in files contain pattern
```bash
sed -i '/.*167\=OPT.*/d' testdata.txt
```

# to select only only one element value of XML file : 
grep -oPm1 "(?<=<TheUniqID>)[^<]+" 

# To check Linux release name
```sh
cat /etc/os-release
```

# How to check whether your linux is 32bit or 64 bit 
To run "arch" command,  this is similar to "uname -m" , it prints to the screen whether your system is running 32-bit (“i686”) or 64-bit (“x86_64”).

# convert line ending to unix (sometimes git submit is dos format)
```sh
dos2unix the_script_file_name
```

# To check redhat Linux version
```sh
cat  /etc/redhat-release
```

# To list all users in linux
```sh
cat /etc/passwd
```


# Show IP address in Linux
```sh
$ifconfig
eth0      Link encap:Ethernet  HWaddr 00:50:56:9B:19:81
          inet addr:133.14.16.5  Bcast:133.14.16.255  Mask:255.255.255.0
```

# Check system resource
```sh
execute `cat /proc/cpuinfo` and `free -m` to gain information about the server’s CPU and memory.
```

# chmod command
From one to four octal digits
Any omitted digits are assumed to be leading zeros. 

The first digit = selects attributes for the set user ID (4) and set group ID (2) and save text image (1)S
The second digit = permissions for the user who owns the file: read (4), write (2), and execute (1)
The third digit = permissions for other users in the file's group: read (4), write (2), and execute (1)
The fourth digit = permissions for other users NOT in the file's group: read (4), write (2), and execute (1)

The octal (0-7) value is calculated by adding up the values for each digit
User (rwx) = 4+2+1 = 7
Group(rx) = 4+1 = 5
World (rx) = 4+1 = 5
chmode mode = 0755

Examples
```sh
chmod 400 file - Read by owner
chmod 040 file - Read by group
chmod 004 file - Read by world 

chmod 200 file - Write by owner
chmod 020 file - Write by group
chmod 002 file - Write by world
```

# top
- enter u, then user id to show only user process
- Z: global color scheme, e.g. red or green
- B: global bold for all
- z: show color, then b to hightlight, and x highlight sort fidl, y highlight running tasks
- #3: show only 3 threads
- c: show command line
- F: sort, e.g. Fk sort by CPU%
- R: reverse order

# Sample config files 

## .vimrc

```sh

set number
set incsearch
set hlsearch
syntax on
colorscheme desert
```

## ==== screenrc  =
https://gist.githubusercontent.com/ChrisWills/1337178/raw/8275b66c3ea86a562cdaa16f1cc6d9931d521e1b/.screenrc-main-example
```sh
# GNU Screen - main configuration file 
# All other .screenrc files will source this file to inherit settings.
# Author: Christian Wills - cwills.sys@gmail.com

# Allow bold colors - necessary for some reason
attrcolor b ".I"

# Tell screen how to set colors. AB = background, AF=foreground
termcapinfo xterm 'Co#256:AB=\E[48;5;%dm:AF=\E[38;5;%dm'

# Enables use of shift-PgUp and shift-PgDn
termcapinfo xterm|xterms|xs|rxvt ti@:te@

# Erase background with current bg color
defbce "on"

# Enable 256 color term
term xterm-256color

# Cache 30000 lines for scroll back
defscrollback 30000

# New mail notification
# backtick 101 30 15 $HOME/bin/mailstatus.sh

hardstatus alwayslastline 
# Very nice tabbed colored hardstatus line
hardstatus string '%{= Kd} %{= Kd}%-w%{= Kr}[%{= KW}%n %t%{= Kr}]%{= Kd}%+w %-= %{KG} %H%{KW}|%{KY}%101`%{KW}|%D %M %d %Y%{= Kc} %C%A%{-}'

# change command character from ctrl-a to ctrl-b (emacs users may want this)
#escape ^Bb

# Hide hardstatus: ctrl-a f 
bind f eval "hardstatus ignore"
# Show hardstatus: ctrl-a F
bind F eval "hardstatus alwayslastline"
```

## ====================.bashrc ==========
```sh
# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi
# source ./prompt
export PS1=''

export PS1='[\e[104mLight blue \u \A\]$ '

export PS1="\[\e[32m\]\u@\h \d \t \w \[\e[m\] \\$"

\e[104mLight blue

# Welcome message
echo -ne "Good Morning ! It's "; date '+%A, %B %-d %Y'
echo -e "And now your moment of Zen:"; fortune
echo
echo "Hardware Information:"
sensors  # Needs: 'sudo apt-get install lm-sensors'
uptime   # Needs: 'sudo apt-get install lsscsi'
free -m

# User specific aliases and functions

PS1='\[`[ $? = 0 ] && X=2 || X=1; tput setaf $X`\]\h\[`tput sgr0`\]:$PWD\n\$ '

============vimrc =========
set number
set incsearch
set hlsearch

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

grep -v "unwanted_word" file | grep XXXXXXXX

// find command exclude “permission denied”
$ find . -name "java" 2>/dev/null
```



# Passwordless connection in putty
```sh
1. Generate Public & private key pair by keygen
2. Log into Linux, nano .ssh/authorized_keys and paste the public key
3. Save the private key in putty and load it in Putty session
```

# find java files older than 3 days
```sh
find . -name "*.java" -atime -3d
```

# Remove capitalization
```sh
sed -ie 's/Return /return /g' ReverseString.java 
```

# replace string in files
```sh
#grep -r "pack.*me" .
sed -ie 's/package.*me.*;/package com.todzhang;/g' *.java
sed -ie 's/package me.todzhang;/package com.todzhang;/g' ~/dev/git/algo/algoWS/src/main/java/com/todzhang/*.java
```
# to update layout from post to posts for jekyll in batch
sed -ie 's/layout: posts/layout: posts/g' _posts/2016-06-03*.md 


layout: posts

# create directory hierarchy via path
```sh
mkdir -p ~/abc/def/egg
```

`-p` means create intermediary folders, if not exist. Those intermediary folders with permission 777

# lsof to locate whether/who allocated port 8080
`lsof` means list open files.
```sh
lsof -n -P -i | grep 8080
```

# To get rid of ''
Sometimes got "403 Forbidden" error when trying to downalod file via wget, e.g.

```sh
$ wget http://www.xmind.net/xmind/downloads/xmind-7.5-update1-macosx.dmg
--2016-09-09 23:27:29--  http://www.xmind.net/xmind/downloads/xmind-7.5-update1-macosx.dmg
Resolving www.xmind.net... 23.23.188.223
Connecting to www.xmind.net|23.23.188.223|:80... connected.
HTTP request sent, awaiting response... 403 Forbidden
2016-09-09 23:27:29 ERROR 403: Forbidden.
```

To solve this problem, using following syntax, adding `-U xx`

```sh
wget -U 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.6) Gecko/20070802 SeaMonkey/1.1.4' http://www.xmind.net/xmind/downloads/xmind-7.5-update1-macosx.dmg
```

# case insensitive ls command in bash
Update .bashrc or current active window
```sh
shopt -s nocaseglob
```
# one line command to download and extract files

```sh
$cd /tmp;curl https://www.kernel.org/pub/linux/utils/util-linux/v2.24/util-linux-2.24.tar.gz	| tar -zxf-;cd	util-linux-2.24;
```

# Redirect request for HTTP 3xxx code
```sh
curl -LSso ~/.vim/autoload/pathogen.vim https://tpo.pe/pathogen.vim
```

`-L` means redirect upon HTTP code 3xxx
`-Ss` work together to make the curl show errors if there are
`-o` means output to a specified file, rather than stdout

# search files contains keyword
```sh
grep -ri 'architect' . | awk -F ':' '{print $1}'
```

# Show Linux kernel and name
## lsb_release
`lsb` means Linux Standard Base , `-a` means print all information
```sh
lsb_release -a -u
```
will output
```sh
phray@phray-VirtualBox ~ $ lsb_release -a -u
No LSB modules are available.
Distributor ID:	Ubuntu
Description:	Ubuntu 14.04 LTS
Release:	14.04
Codename:	trusty
```
## /etc/os-release
```sh
cat /etc/os-release
```
will output Following
```sh
phray@phray-VirtualBox ~ $ cat /etc/os-release
NAME="Ubuntu"
VERSION="14.04.2 LTS, Trusty Tahr"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 14.04.2 LTS"
VERSION_ID="14.04"
HOME_URL="http://www.ubuntu.com/"
SUPPORT_URL="http://help.ubuntu.com/"
BUG_REPORT_URL="http://bugs.launchpad.net/ubuntu/"
```

Following is the command found in docker.sh
```sh
lsb_dist=$(lsb_release -a -u 2>&1 | tr '[:upper:]' '[:lower:]' | grep -E 'id' | cut -d ':' -f 2 | tr -d '[[:space:]]')
```

show the 2nd column
```sh
lsb_release --Codename | cut -f2
```

## gpsswd

DESCRIPTION
gpasswd is used to administer the /etc/group file (and /etc/gshadow file if compiled with SHADOWGRP defined). Every group can have administrators, members and a password. System administrator can use -A option to define group administrator(s) and -M option to define members and has all rights of group administrators and members.

Notes about group passwords
Group passwords are an inherent security problem since more than one person is permitted to know the password. However, groups are a useful tool for permitting co-operation between different users.

OPTIONS
Group administrator can add and delete users using -a and -d options respectively. Administrators can use -r option to remove group password. When no password is set only group members can use newgrp to join the group. Option -R disables access via a password to the group through newgrp command (however members will still be able to switch to this group).

gpasswd called by a group administrator with group name only prompts for the group password. If password is set the members can still newgrp(1) without a password, non-members must supply the password.

FILES
Tag	Description
/etc/group
 	Group account information.
/etc/gshadow
 	Secure group account information.

```sh
sudo gpasswd -a USER docker
```


# Compare files difference in two folders
```sh
diff -rq ~/dev/pa ~/dev/hexo/myblog/source/_posts
```
This used option `-r` (recursive) and `-q` quite, means only show differences

# To execut shell/unix command within vim
```sh
:~ls -lt
```

# To open find result with sublime
```sh
find . -name "*Linux*.md" | xargs sublime 
find . -name "*Linux*.md" | xargs sublime ~ # open in new Sublime window
```

# To vim/vim edit directly on file output by find command
```sh
find . -name "*tmux*" -exec vim {} \;
```

Be advised you may experience following error message
> find: missing argument to `-exec'

actually you should add a slash in front of semi colon

# quite mode in apt-get
- apt-get will in verbose mode
- apt-get `-q` will be in less verbose , a.k.a quite mode
- apt-get `-qq` in extreme least verbose mode

