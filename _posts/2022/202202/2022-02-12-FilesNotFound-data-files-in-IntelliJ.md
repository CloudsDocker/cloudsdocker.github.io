---
header:
    image: /assets/images/hd_FileNotFoundException.png
title:  FileNotFound Exception when loading  data file in IntelliJ
date: 2022-02-12
tags:
 - IntelliJ
 - Java
 
permalink: /blogs/tech/en/FileNotFoundException_Data_File_IntelliJ
layout: single
category: tech
---

> Take time to do what makes your soul happy!


# Background & symptoms

To share and process data via text file is a very common way in system design and communication.

By existing API, it's very straightforward to load files line by line, here is a sample code block in IntelliJ which trying to load a file (comma separated) called `abc.txt`. 

However, when yo hit run and expected to print content

```java

public class DataParser {
    public static void main(String[] args) {
try (FileReader fileReader = new FileReader("abc.txt")) {
            try (Scanner scanner = new Scanner(fileReader)) {
                while (scanner.hasNext()) {
                    String[] parts = scanner.nextLine().split(",");
                     System.out.println(parts);

                }
            }
    }
}
```

While unfortunately you get an exception

```bash
java.io.FileNotFoundException: abc.txt (No such file or directory)
	at java.base/java.io.FileInputStream.open0(Native Method)
	at java.base/java.io.FileInputStream.open(FileInputStream.java:216)
	at java.base/java.io.FileInputStream.<init>(FileInputStream.java:157)
	at java.base/java.io.FileInputStream.<init>(FileInputStream.java:111)

```


## Output preview

![output](/assets/images/FileNotFoundException.png)



## Troubleshooting
You are pretty sure the file abc.txt just sit under the same folder of this java class. 

You tell yourself should calm down, no panic. 
> This is just a piece of cake. 
Then copy this abc.txt under folder `resources` and expect all good for rerun.

Unfortunately you get same hatred exception.

# Solution

This is actually one `bug` or `trick` in IntelliJ setup and configuration for run Java.

As below screenshot, please check your current `Working directory`, if its your project `java/main`, then you should copy and put your abc.txt file under there.  e.g. to `/src/java/main/abc.txt`

![output](/assets/images/FileNotFoundExceptionSolution.png)


Once above quick fix done, rerun you'll get your expected data loaded successfully.





--End--



