---
title: How To Config JFR Java Flight Control
header:
    image: /assets/images/How_to_config_JFR.jpg
date: 2023-03-14
tags:
 - JFR
 - Java
 - PerformanceTuning

permalink: /blogs/tech/en/How_to_config_JFR
layout: single
category: tech
---
> "Climb the mountains and get their good tidings. Nature's peace will flow into you as sunshine flows into trees. The winds will blow their own freshness into you, and the storms their energy, while cares will drop away from you like the leaves of Autumn." — John Muir

# How to config JFR Java Flight Control to keep running in 1 minute

Starting JFR (Java Flight Recorder) can be done in a few simple steps. Here's how you can start JFR in 1 minute:

Open a terminal or command prompt window.

Navigate to the directory where your Java installation is located.

Type the following command to start JFR:

```bash
java -XX:+UnlockCommercialFeatures -XX:+FlightRecorder -XX:StartFlightRecording=duration=60s,filename=myrecording.jfr

```
This command starts JFR and records data for 60 seconds to a file called "myrecording.jfr". You can adjust the duration and filename as needed.

After 60 seconds, JFR will automatically stop recording and save the file.

To view the recording, you can use the Java Mission Control tool, which is included with Java SE Advanced and Java SE Suite. Simply open Java Mission Control, select the "Flight Recorder" tab, and open the recording file.

That's it! By following these steps, you can start JFR and record data in just 1 minute.


# How to set maximum age of the recorded data that should be included in the generated JFR file.
The jcmd command is used to send diagnostic commands to a running Java Virtual Machine (JVM). One of the commands that can be sent is to start a Java Flight Recorder (JFR) recording. The maxage parameter in the jcmd command specifies the maximum age of the recorded data in seconds.

When a JFR recording is started, it starts collecting data from the JVM. The maxage parameter specifies how long the JFR recording should continue before automatically stopping. After the specified number of seconds has passed, the recording will stop and the recorded data will be saved to a file.

For example, to start a JFR recording with a maximum age of 60 seconds, you can use the following jcmd command:

```shell
jcmd <pid> JFR.start maxage=60s filename=myrecording.jfr

```
In this command, <pid> is the process ID of the JVM that you want to record, maxage=60s specifies the maximum age of the recording in seconds, and filename=myrecording.jfr specifies the name of the file where the recorded data will be saved.

# How to touch a JFR file

If you want to start a JFR recording with a maximum age of 0 seconds, you can use the following jcmd command:

```shell
jcmd <pid> JFR.start maxage=0 filename=myrecording.jfr
```
In this case, the JFR recording will start and immediately stop, and the recorded data will be saved to the specified file.

It's worth noting that the maxage parameter is just one of several options that can be specified when starting a JFR recording with the jcmd command. Other options include specifying the recording name, the duration of the recording, and the event settings to be included in the recording. You can view the full list of options by running the following command:
```shell
jcmd <pid> JFR.start help
```

This will display the available options and their descriptions.

--End--
