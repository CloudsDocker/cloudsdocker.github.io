---
header:
    image: /assets/images/how_to_save_expect_script_run_output_to_file_locally.jpg
title:  How to save expect script run output to file locally
date: 2023-03-02
tags:
 - Expect
 - AI
 - Automation
 
permalink: /blogs/tech/en/how_to_save_expect_script_run_output_to_file_locally
layout: single
category: tech
---

> Nothing is as easy as it looks.

# How to save expect script run output to file locally

To save the output of an expect script to a file locally, you can use the "log_file" command in your expect script. Here's an example of how to do this:
```perl
#!/usr/bin/expect -f

# Set the log file name
set log_file_name "output.log"

# Open the log file
log_file -a $log_file_name

# Run your commands here
# ...

# Close the log file
log_file close

```

In the above script, the "log_file" command is used to open a log file named "output.log" in append mode. This means that any output generated by the expect script will be added to the end of the file, rather than overwriting any existing content.

You can customize the name of the log file by setting the "log_file_name" variable to the desired file name. You can also change the mode of the log file to "w" (write) instead of "a" (append) if you want to overwrite the file instead of appending to it.

Once you've run your expect script, the output will be saved to the specified log file on your local machine.



--HTH--


