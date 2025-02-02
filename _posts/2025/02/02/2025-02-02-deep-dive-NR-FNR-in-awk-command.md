---
header:
    image: /assets/images/hd_algo_big_H.png
title:  deep dive NR and FNR in linux awk command
date: 2025-02-02
tags:
    - tech
permalink: /blogs/tech/en/deep-dive-NR-awk-command
layout: single
category: tech
---
> Your time is limited, don't waste it living someone else's life. - Steve Jobs

# deep dive NR awk command
# Mastering `awk` and `NR`: Unlocking the Power of Line Processing in Linux

In the world of Linux system administration and Site Reliability Engineering (SRE), efficient text processing is essential. One of the most powerful tools for this is `awk`, and at the heart of its capabilities is the `NR` variable. This guide explores how to leverage `NR` for advanced text processing, log analysis, and automation.

---

## Understanding `NR` in `awk`
`NR` (Number of Records) is a built-in `awk` variable that represents the **current line number** being processed. It starts at `1` and increments with each new line of input.

### **Basic Usage of `NR`**
To print each line along with its line number:
```bash
awk '{print NR, $0}' file.txt
```
#### **Example Input (file.txt)**:
```
apple
banana
cherry
date
elderberry
```
#### **Output**:
```
1 apple
2 banana
3 cherry
4 date
5 elderberry
```

---

## **Filtering with `NR`**
One of the most powerful use cases of `NR` is filtering lines based on their number.

### **Print the 5th Line**
```bash
awk 'NR==5' file.txt
```
**Output:**
```
elderberry
```

### **Print Lines from 5 to 10**
```bash
awk 'NR>=5 && NR<=10' file.txt
```

### **Skip the First 5 Lines (Equivalent to `tail -n +6`)**
```bash
awk 'NR>5' file.txt
```

## Practical SRE Use Cases
### Log Monitoring: Show the Last 10 Lines
Equivalent to tail -n 10:

```bash
awk 'NR>(NR-10)' log.txt
```

### Filtering Specific Events
Extracts the first field (timestamp) of error logs from the 50th line onward:

```bash
awk 'NR>=50 && /ERROR/ {print $1}' app.log
```

---

## **`NR` vs `FNR`: Handling Multiple Files**
While `NR` counts **globally** across all files, `FNR` (File Number of Records) counts separately for each file.

### **Example: Printing Line Numbers for Multiple Files**
```bash
awk '{print FNR, NR, $0}' file1.txt file2.txt
```
#### **If `file1.txt` contains:**
```
A1
A2
A3
```
#### **And `file2.txt` contains:**
```
B1
B2
```
#### **Output:**
```
1 1 A1
2 2 A2
3 3 A3
1 4 B1
2 5 B2
```
- `FNR` resets for `file2.txt`, while `NR` continues counting.

---

## **Real-World Use Cases for SREs and Developers**

### **1. Log File Analysis: Extracting Key Information**
To extract timestamps from an Apache log (only from the 100th line onward):
```bash
awk 'NR>=100 {print $4}' access.log
```

### **2. Automating Process Monitoring**
To display only the username and process ID of the 5th running process:
```bash
ps aux | awk 'NR==5 {print $1 ":" $2}'
```

### **3. Extracting the Last 10 Lines of a Log File**
Equivalent to `tail -n 10`:
```bash
awk 'NR>(NR-10)' log.txt
```

---

## **Final Thoughts**
Understanding and leveraging `NR` in `awk` unlocks incredible possibilities for **text processing, automation, and log analysis**. Whether you're troubleshooting servers or parsing structured data, `awk` remains a must-know tool in any Linux user's arsenal.

Stay tuned for more deep dives into Linux command-line mastery!

