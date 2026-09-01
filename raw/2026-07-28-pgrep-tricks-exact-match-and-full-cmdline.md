---
title: "pgrep 骚操作:精确匹配 -x 与命令行正则 -f"
date: 2026-07-28
categories: [engineering, shell]
tags: [linux, pgrep, shell, cli, debugging, process-management]
---

`pgrep` 看着是个三行代码就能写出来的小工具,但里面的坑和骚操作比想象中多。这篇整理两个最实用的用法:精确匹配进程名,和用正则抓完整命令行。

## 快速回顾:基本用法

`pgrep -a 'sshd'` → 列出所有命令行匹配 `sshd` 的进程,带完整命令行(`-a` = show argv)。

```
1234 /usr/sbin/sshd -D
```

## 1. 精确匹配 `-x`

`pgrep` 默认是**子串匹配**——`pgrep sshd` 会把 `sshd`、`sshd-session`、`my-sshd-wrapper` 全部匹配上,坑就坑在这里。

```bash
pgrep -a -x sshd      # 进程名必须完全等于 sshd
```

`-x` 只对**进程名**(comm,15字符截断)做精确匹配,不是对整条命令行。所以 `/usr/sbin/sshd -D` 依然能匹配,因为进程名是 `sshd`,只是不会误伤 `sshd-session`。

**坑点**:Linux 内核里进程名(`/proc/pid/comm`)只有 15 字节,长名字会被截断,`-x` 精确匹配是按截断后的名字比对的,偶尔会有反直觉的结果。

## 2. `-f` 匹配整条命令行 + 正则

```bash
pgrep -a -f 'sshd.*22'
```

`-f` 把匹配对象从"进程名"换成 `/proc/pid/cmdline`(完整命令行,含所有参数)。这时候你就能用**标准 POSIX 扩展正则**去抓任何藏在参数里的东西。

实用套路:

```bash
pgrep -af 'python.*manage.py'      # 抓某个 django 项目进程,不管 python 版本路径
pgrep -af 'node.*--port[= ]3000'   # 抓监听特定端口的 node 进程
pgrep -af 'airflow.*scheduler'     # 抓 airflow scheduler 进程
```

**核心区别一句话**:不加 `-f` 是拿正则去匹进程名(短、快、不容易误伤);加 `-f` 是拿正则去匹整条命令行(能抓参数,但容易连自己敲的这条 `pgrep` 命令本身一起匹配进去——因为 grep 类命令的 argv 里正好也含有你的关键词)。

### 经典翻车现场

```
$ pgrep -af 'sshd'
1234 /usr/sbin/sshd -D
5678 pgrep -af sshd     # ← 把自己也算进去了!
```

解法:`pgrep -af '[s]shd'`(方括号技巧让 grep 自身的 argv 里的 `sshd` 变成 `[s]shd`,正则不匹配自己)。这招在 `ps aux | grep` 时代就是经典梗,pgrep/grep 都适用。
