---
header:
    image: /assets/images/hd_cpu_system_info_aws.jpg
title:  How to check your CPU model and Linux distribution in your AWS VM
date: 2023-01-10
tags:
 - AWS
 - CPU
 
permalink: /blogs/tech/en/Check_CPU_Linux_details_in_AWS_EC2
layout: single
category: tech
---

> Lift is short, enjoy the ride.

# How to find your CPU is Graviton or model

To run following command to check your VM hardware details, such the CPU model and baseboard 

## To check your VM type (is it large?)
```shell
sudo dmidecode -t1
```
You'll get following output (sample one)
```shell
Handle 0x0001, DMI type 1, 27 bytes
System Information
        Manufacturer: Amazon EC2
        Product Name: t4g.large
        Version: Not Specified
        Serial Number: ec24f7a0-034a-ac60-1c01-d03ed0ae0484
        UUID: ec24f7a0-034a-ac60-1c01-d03ed0ae0484
        Wake-up Type: Power Switch
        SKU Number: Not Specified
        Family: Not Specified
```

## TO check processor(CPU) information

```shell
sudo dmidecode -t4
```

Here is output of one sample VM in AWS
```shell
Processor Information
        Socket Designation: CPU00
        Type: Central Processor
        Family: ARMv8
        Manufacturer: AWS
        ID: C1 D0 3F 41 00 00 00 00
        Signature: Implementor 0x41, Variant 0x3, Architecture 15, Part 0xd0c, Revision 1
        Version: AWS Graviton2
        Voltage: Unknown
        External Clock: Unknown
        Max Speed: 2500 MHz
        Current Speed: 2500 MHz
        Status: Populated, Enabled
        Upgrade: None
        L1 Cache Handle: Not Provided
        L2 Cache Handle: Not Provided
        L3 Cache Handle: Not Provided
        Serial Number: AWS Graviton2
        Asset Tag: AWS Graviton2
        Part Number: AWS Graviton2
        Core Count: 2
        Core Enabled: 2
        Thread Count: 2
        Characteristics: None
```

## To check base board details
`sudo dmidecode -t2`

```shell
# dmidecode 3.2
Getting SMBIOS data from sysfs.
SMBIOS 3.0.0 present.

Handle 0x0002, DMI type 2, 15 bytes
Base Board Information
        Manufacturer: Amazon EC2
        Product Name: Not Specified
        Version: Not Specified
        Serial Number: Not Specified
        Asset Tag: i-000ddf9ac579ec970
        Features: None
        Location In Chassis: Not Specified
        Chassis Handle: 0x0003
        Type: Other
        Contained Object Handles: 0

```

# How to know your OS (linux) distribution details in VM

Is my EC2 running in redhat or any type of linux, to run following command

```shell
cat /etc/os-release
```
Then you'll get more details as below, including linux distribution, version and internal version number etc.

```shell
NAME="Amazon Linux"
VERSION="2"
ID="amzn"
ID_LIKE="centos rhel fedora"
VERSION_ID="2"
PRETTY_NAME="Amazon Linux 2"
ANSI_COLOR="0;33"
CPE_NAME="cpe:2.3:o:amazon:amazon_linux:2"
HOME_URL="https://amazonlinux.com/"
```


--HTH--



