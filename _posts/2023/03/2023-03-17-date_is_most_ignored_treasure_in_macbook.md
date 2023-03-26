---
title: Date Is The Most Ignored Treasure In Macbook
header:
    image: /assets/images/date_is_most_ignored_treasure_in_macbook.jpg
date: 2023-03-17
tags:
 - JFR
 - Java
 - PerformanceTuning

permalink: /blogs/tech/en/date_is_most_ignored_treasure_in_macbook
layout: single
category: tech
---
> "The only way to do great work is to love what you do." - Steve Jobs

# date command is a treasure in macbook

`Date` command, which is one macbook built-in command.
I think this is the most ignored command on the MacBook.
Let’s do a quick check of quiz to see. How familiar are you are with date in Macbook?

#1: 
```shell
date -r 1647654000
``` 
and 

#2:
```shell
echo "$(date +%s)000"
``` 

and 

#3:
```shell
date -v +1w
``` 

#4:
```shell
date -v wednesday 
```

This will output the date and time of the same day next week in your local timezone.

### Answers!
1: To convert a Unix timestamp (i.e., number of seconds since the Unix epoch) to a human-readable date and time, use the date command with the -r option and the timestamp value:
2: To get the current time in milliseconds, you can use the date command along with the %s format string and the echo command to append the milliseconds:
3: This will output the current time in milliseconds.
4: show what's the date of this Wednesday

Very interesting and seems you are ignored such useful tool, and sometimes you need to search some online tool or even `reinvent-your-wheels`


## Quick introduction for date command
As a macOS user, you may have encountered the "date" command in your terminal window. This command is a simple yet powerful tool that allows you to display and modify the date and time information of your system. In this blog post, we will explore the various uses of the "date" command in macOS.

Displaying the Current Date and Time
The most basic use of the "date" command is to display the current date and time on your system. To do this, simply open your terminal window and type "date" followed by the return key. The output will show you the current date and time in your system's default time zone.

Formatting the Date and Time
The "date" command allows you to customize the way the date and time are displayed by using formatting codes. These codes are preceded by a plus sign (+) and are used to specify the order and format of the date and time information. For example, if you wanted to display the date in the format of "YYYY-MM-DD", you would type "date +'%Y-%m-%d'" in your terminal window. Here are some commonly used formatting codes:

 - %Y - Year with century (e.g., 2023)
 - %m - Month (01-12)
 - %d - Day of the month (01-31)
 - %H - Hour (00-23)
 - %M - Minute (00-59)
 - %S - Second (00-60)

### Modifying the Date and Time
In addition to displaying the date and time, the "date" command also allows you to modify it. This can be useful if you need to set the system clock to a specific date and time or adjust it for time zone changes. To modify the date and time, you will need to use the "sudo" command to gain administrative privileges. Here are some examples of how to modify the date and time:

 _ Set the date and time to a specific value: sudo date 031612002023 (this sets the date to March 16th, 2023 at 12:00 AM)
 _ Set the date and time using a formatted string: sudo date -j -f "%Y-%m-%d %H:%M:%S" "2023-03-16 12:00:00" (this sets the date and time to March 16th, 2023 at 12:00 PM using the specified format)
 _ Adjust the date and time by a certain amount: sudo date -v +1d (this adds one day to the current date)

## Conclusion
The "date" command is a versatile tool that can be used to display and modify the date and time information on your macOS system. Whether you need to check the current time, customize the date format, or adjust the system clock, the "date" command is a quick and easy solution. By using the various formatting codes and modification options, you can customize the date and time to suit your needs.

## Script bible for this treasure command

### macbook command line to get what date of this wendday

You can use the date command on your MacBook's command line to get the date of this Wednesday. Here's the command you can use:

```shell
date -v wednesday +%Y-%m-%d
```
This command uses the -v option to specify a relative date, and wednesday to indicate the next Wednesday. The +%Y-%m-%d option formats the output as a date string in the format 'YYYY-MM-DD'.

So if you run this command today (assuming today is not Wednesday), it will give you the date of the upcoming Wednesday. For example, if today is Monday, March 21, 2023, the command will return '2023-03-23' which is the date of the next Wednesday.


### To display the current date and time, use the date command without any options:

```shell
date
``` 
This will output the current date and time in your local timezone.

### To display the current date in a specific timezone, use the -u option followed by the timezone identifier:

```shell
date -u +"%Y-%m-%d %H:%M:%S" -d "TZ=\"America/New_York\""
``` 
This command will output the current date and time in the Eastern Time (ET) timezone. You can replace "America/New_York" with the timezone identifier of your choice.

### To display the date and time of a specific day in the past or future, use the -v option followed by a relative date. For example, to display the date and time of the same day next week:

```shell
date -v +1w
``` 
This will output the date and time of the same day next week in your local timezone.

### To display the date and time in a specific format, use the + option followed by the format string. For example, to display the date and time in the format 'YYYY-MM-DD HH:MM:SS':

```shell
date +"%Y-%m-%d %H:%M:%S"
``` 
This will output the current date and time in the specified format.

### To convert a date or time from one format to another, use the date command with the -j option and the input and output format strings. For example, to convert a date string in the format 'MM/DD/YYYY' to the format 'YYYY-MM-DD':
```shell

date -j -f "%m/%d/%Y" "03/16/2023" "+%Y-%m-%d"
``` 
This will output the date '2023-03-16', which is the input date string converted to the output format.

### To display the number of seconds since the Unix epoch (January 1, 1970), use the date command with the %s format string:

```shell

date "+%s"
``` 
This will output the current number of seconds since the Unix epoch.

### To display the number of seconds between two dates or times, use the date command with the -j option and the input and output format strings, and subtract the two values:

```shell

start=$(date -j -f "%Y-%m-%d %H:%M:%S" "2023-03-16 09:00:00" "+%s")
end=$(date -j -f "%Y-%m-%d %H:%M:%S" "2023-03-18 15:00:00" "+%s")
echo $((end - start))
``` 
This will output the number of seconds between the two dates and times '2023-03-16 09:00:00' and '2023-03-18 15:00:00', which is 216000 seconds (2 days * 24 hours/day * 60 minutes/hour * 60 seconds/minute).


### To display a countdown timer in the command line, you can use the sleep command along with the date command to calculate the remaining time:

```shell

SECONDS=300  # 5 minutes
while [ $SECONDS -gt 0 ]; do
echo "Time remaining: $(date -u --date @$SECONDS +%M:%S)"
sleep 1
SECONDS=$((SECONDS - 1))
done
This will display a countdown timer for 5 minutes (300 seconds) in the command line, updating the remaining time every second.
``` 
--End--
