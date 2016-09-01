---
layout: page
title: Linux Tips
tag:
- Linux
---
# case insensitive ls command in bash
Update .bashrc or current active window
```sh
shopt -s nocaseglob
```
# one line command to download and extract files

```sh
$cd /tmp;curl https://www.kernel.org/pub/linux/utils/util-linux/v2.24/util-linux-2.24.tar.gz	| tar -zxf-;cd	util-linux-2.24;
```
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
