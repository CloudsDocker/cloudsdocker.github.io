---
title: know in and out of free command
header:
    image: /assets/images/GoogleMap_missing_JPN.jpg
date: 2023-04-05
tags:
- linux
- devops
- automation

permalink: /blogs/tech/en/know-in-and-out-of-free-command
layout: single
category: tech
---

> You are not a drop in the ocean, you are the entire ocean in a drop.

# Command to check memory usage in Linux
To show the current free memory on Linux, you can use the "free" command in the terminal.

Open your terminal and type the following command:


```shell
free -h
```
This will display the current memory usage statistics in a human-readable format, including the total amount of memory, the amount used, and the amount free.

The "-h" option stands for "human-readable" and displays the memory sizes in a format that is easier to read for humans (e.g. using units like MB or GB).

Alternatively, you can also use the "top" command, which displays real-time information about the system's performance, including memory usage. To use the "top" command, type the following in the terminal:

```shell
top
```
This will display a list of running processes and their respective memory usage statistics. The total amount of memory and free memory will also be displayed at the top of the screen. To exit the "top" command, press "q".

# what's each column in "free" command output?
The "free" command in Linux displays the current memory usage statistics. The output of the command includes the following columns:

 - total: This column shows the total amount of physical memory (RAM) in the system.
 - used: This column shows the amount of RAM that is currently being used by the system.
 - free: This column shows the amount of RAM that is currently not being used by the system and is available for use.
 - shared: This column shows the amount of RAM that is being shared by multiple processes.
 - buff/cache: This column shows the amount of RAM that is being used by the system for buffering and caching data.
 - available: This column shows the amount of RAM that is currently available for use by applications and processes.

The units for memory size used in the output are usually displayed in kilobytes (KB) or megabytes (MB), depending on the amount of memory installed on the system. The "-h" option can be used with the "free" command to display the memory sizes in a human-readable format, using units like MB or GB.

# what's the buff cache used for?
In Linux, the "buff/cache" column in the output of the "free" command shows the amount of memory that is being used by the system for buffering and caching data.

When a program reads data from a file or disk, the data is first read into a buffer in memory, from where it can be quickly accessed by the program. Similarly, when a program writes data to a file or disk, the data is first written to a buffer in memory, which is then periodically flushed to the disk. This helps to reduce the number of disk I/O operations, which are generally slower than memory operations, and can improve overall system performance.

In addition to buffering data for I/O operations, the Linux kernel also uses a portion of the available memory for caching frequently accessed files and data from disk. This cache is used to speed up file system operations by keeping frequently used files and data in memory, which can be accessed much faster than reading from the disk.

The buff/cache memory is not considered to be "used" memory as it can be quickly freed up if an application or process requires more memory. When a program requests more memory, the kernel can reclaim the memory used for buffering and caching and allocate it to the requesting program, providing more memory resources for applications and processes when needed.

--HTH--
