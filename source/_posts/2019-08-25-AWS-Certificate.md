---
title: AWS certification
tags:
- AWS
- Cloud
---

# Concepting

Cloud computing is the on-demand delivery of IT resources and applications via the Internet with pay-as-you-go pricing. Whether you run applications that share photos to millions of mobile users or deliver services that support the critical operations of your business, the cloud provides rapid access to flexible and low-cost IT resources.

In its simplest form, cloud computing `provides an easy way to access servers, storage`, databases, and a broad set of application services `over the Internet`.

# Benefits of AWS

There are six advantages for AWS clouding

 1. Global in minutes
 1. Variable vs capital expense
 1. Economies of scale
 1. Stop guessing capacity
 1. Focus on business differentaiors
 1. Increate speed and agility 

## Cost saving
One of the key benefits of cloud computing is the opportunity to `replace up-front capital infrastructure expenses with low variable costs` that scale with your business. With the cloud, businesses no longer need to plan for and procure servers and other IT infrastructure weeks or months in advance. Instead, they can instantly spin up hundres or thousands of servers in minutes and deliver results faster.

With pay-per-use billing, AWS clouding services `become an operational expense instead of a capital expense`.



# Metadata

Metadata, known as tags, that you can create and assign to your Amazon EC2 resources

Amazon Web Services. Amazon Elastic Compute Cloud (Kindle Location 152). Amazon Web Services. Kindle Edition. 

# AZ (Available Zones)
- Each availability zone is a physical data center in the region, but separate from the other ones (so that they’re isolated from disasters)
- AWS Consoles are region scoped (except IAM, S3 & Route53)


# EC2
Here you need to create an AMI, but because AMI are bounded in the regions they are created, they need to be copied across regions for disaster recovery purposes

## Placement group
 Placements groups are the answer here, where "cluster" guarantees high network performance (correct answer), whereas "spread" would guarantee independent failures between instances.

## ASG

### ASG Lauch configuration

Launch configurations are immutable meaning they cannot be updated. You have to create a new launch configuration, attach it to the ASG and then terminate old instances / launch new instances

### ASG termination
AZs will be balanced first, then the instance with the oldest launch configuration within that AZ will be terminated. For a reference to the default termination policy logic, have a look at this link: https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-instance-termination.html

# IAM
Your whole AWS security is there: 
• Users
• Groups 
• Roles

Policies are written in JSON (JavaScript Object Notation)

IAM has a `global` view

## IAM Federation
• Big enterprises usually integrate their own repository of users with IAM 
• This way, one can login into AWS using their company credentials
• Identity Federation uses the SAML standard (Active Directory)

• One IAM User per PHYSICAL PERSON
• One IAM Role per Application


# Storage
### Performance
Instance Store will have the highest disk performance but comes with the storage being wiped if the instance is terminated, which is acceptable in this case. EBS volumes would provide good performance as far as disk goes, but not as good as Instance Store. EBS data survives instance termination or reboots. EFS is a network drive, and finally S3 cannot be mounted as a local disk (natively).

Need to define two terms:
• RPO: Recovery Point Objective
• RTO: Recovery Time Objective

## S3
Generating S3 pre-signed URLs would bypass CloudFront, therefore we should use CloudFront signed URL. To generate that URL we must code, and Lambda is the perfect tool for running that code on the fly. 

As the file is greater than 5GB in size, you must use Multi Part upload to upload that file to S3.

### Encryption
With SSE-C, your company can still provide the encryption key but let AWS do the encryption

## EBS (Elastic Block Storage)
EBS is already redundant storage (replicated within an AZ)
But what if you want to increase IOPS to say 100 000 IOPS?

### RAID
#### RAID 0 (increase performance)
 EC2 instance
One logical volume
either
EBS Volume 1
• Combining 2 or more volumes and getting the total disk space and I/O
• But one disk fails, all the data is failed

#### RAID 1 (increase fault tolerance)
 EC2 instance
One logical volume
both
• RAID 1 = Mirroring a volume to another
• If one disk fails, our logical volume is still working
• We have to send the data to two EBS volume at the same time (2x network)

### EBS types
 keeping as io1 but reducing the iops may interfere with the burst of performance we need. The EC2 instance type changes won't affect the 90% of the costs that are incurred to us. CloudFormation is a free service to use. Therefore, gp2 is the right choice, allowing us to save on cost while keeping a burst in performance when needed


#### Save network cost
 S3 would imply changing the application code, Glacier is not applicable as the files are frequently requested, Storage Gateway isn't for distributing files to end users. CloudFront is the right answer, because we can put it in front of our ASG and leverage a Global Caching feature that will help us distribute the content reliably with dramatically reduced costs (the ASG won't need to scale as much)


## EFS
Instance Stores or EBS volumes are local disks and cannot be shared across instances. Here, we need a network file system (NFS), which is exactly what EFS is designed for.

# VPC

you can optionally connect to your own network, known as virtual private clouds (VPCs)

Amazon Web Services. Amazon Elastic Compute Cloud (Kindle Locations 153-154). Amazon Web Services. Kindle Edition. 

Amazon VPC lets you provision a logically isolated section of the Amazon Web Services (AWS) cloud where you can launch AWS resources in a virtual network that you define. You have complete control over your virtual networking environment, including selection of your own IP address ranges, creation of subnets, and configuration of route tables and network gateways. You can also create a hardware Virtual Private Network (VPN) connection between your corporate datacenter and your VPC and leverage the AWS cloud as an extension of your corporate datacenter.

## VPC Endpoint
You must remember that the two services that use a VPC Endpoint Gateway are Amazon S3 and DynamoDB. The rest are VPC Endpoint Interface

### NACL (Network ACL)
NACL is stateless.

• NACL are like a firewall which control traffic from and to subnet
• Default NACL allows everything outbound and everything inbound
• One NACL per Subnet, new Subnets are assigned the Default NACL
• Define NACL rules:
• Rules have a number (1-32766) and higher precedence with a lower number
• E.g. If you define #100 ALLOW <IP> and #200 DENY <IP> , IP will be allowed • Last rule is an asterisk (*) and denies a request in case of no rule match
• AWS recommends adding rules by increment of 100
• Newly created NACL will deny everything
• NACL are a great way of blocking a specific IP at the subnet level

### NACL noteworhty points
Network ACL Basics

- Your VPC automatically comes with a modifiable default network ACL. By default, it allows all inbound and outbound IPv4 traffic and, if applicable, IPv6 traffic.

### NAT
NAT Instances would work but won't scale and you would have to manage them (as they're EC2 instances). Egress-Only Internet Gateways are for IPv6, not IPv4. Internet Gateways must be deployed in a public subnet. Therefore you must use a NAT Gateway in your public subnet in order to provide internet access to your instances in your private subnets.

# AWS SSM (Simple System Manager)

AWS SSM is parameter store.

# ELB: Elastic Load Balancing

To automatically distribute incoming application traffic across multiple instances, use Elastic Load Balancing. 

For HA, even though our ASG is deployed across 3 AZ, the minimum capacity to be highly available is 2. Finally, we can save costs by reserving these two instances as we know they'll be up and running at any time

## Application Load Balancer vs Network load balancer
Path based routing and host based routing are only available for the Application Load Balancer (ALB). Deploying an NGINX load balancer on EC2 would work but would suffer management and scaling issues. Read more here: https://aws.amazon.com/blogs/aws/new-host-based-routing-support-for-aws-application-load-balancers/

# RDS
RDS stands for Relational Database Service

## Read Replics
RDS Read Replicas for read scalability
- Up to 5 Read Replicas
- Within AZ, Cross AZ or Cross Region
- Replication is ASYNC, so reads are eventually consistent
- Replicas can be promoted to their own DB
- Applications must update the connection string to leverage read replicas

# Elastic Cache
IAM Auth is not supported by ElastiCache

# Amazon CloudWatch

To monitor basic statistics for your instances and Amazon EBS volumes, use Amazon CloudWatch. 

Amazon Web Services. Amazon Elastic Compute Cloud (Kindle Locations 180-184). Amazon Web Services. Kindle Edition. 

# CloudTrail

To monitor the calls made to the Amazon EC2 API for your account, including calls made by the AWS Management Console, command line tools, and other services, use AWS CloudTrail.

In general, to analyze any API calls made within your AWS account, you should use CloudTrail

## Charge
 the first copy of management events is free.

## Cloud Trail retention days
Management event activity is recorded by AWS CloudTrail for the last 90 days, and can be viewed and searched free of charge from the AWS CloudTrail console, or by using the AWS CLI.

# AWS ECS
## Summary: AWS ECS – Elastic Container Service
• ECS is a container orchestration service
• ECS helps you run Docker containers on EC2 machines
• ECS is complicated, and made of:
• “ECS Core”: Running ECS on user-provisioned EC2 instances
• Fargate: Running ECS tasks on AWS-provisioned compute (serverless) 
• EKS: Running ECS on AWS-powered Kubernetes (running on EC2)
• ECR: Docker Container Registry hosted by AWS
• ECS & Docker are very popular for microservices
• For now, for the exam, only “ECS Core” & ECR is in scope 
• IAM security and roles at the ECS task level

## AWS ECS – Concepts
• ECS cluster: set of EC2 instances
• ECS service: applications definitions running on ECS cluster
• ECS tasks + definition: containers running to create the application
• ECS IAM roles: roles assigned to tasks to interact with AWS

## AWS ECS – ALB integration
• Application Load Balancer (ALB) has a direct integration feature with ECS called “port mapping”, This allows you to run multiple instances of the same application on the same EC2 machine

### Dynamic mapping
Dynamic Port Mapping is available for the Application Load Balancer. A reverse proxy solution would work but would be too much work to manage. Here the ALB has a feature that provides a direct dynamic port mapping feature and integration with the ECS service so we will leverage that. Read more here: https://aws.amazon.com/premiumsupport/knowledge-center/dynamic-port-mapping-ecs/

## AWS ECS – ECS Setup & Config file
• Run an EC2 instance, install the ECS agent with ECS config file
• Or use an ECS-ready Linux AMI (still need to modify config file) • ECS Config file is at /etc/ecs/ecs.config

## AWS ECR – Elastic Container Registry
• Store, managed and deploy your containers on AWS
• Fully integrated with IAM & ECS
• Sent over HTTPS (encryption in flight) and encrypted at rest

# Lambda
AWS Lambda functions time out after 15 minutes, and are not usually meant for long running jobs.

# Disaster Recovery
## Overview
Need to define two terms:
• RPO: Recovery Point Objective
• RTO: Recover y Time Objective

Disaster Recovery Strategies
• Backup and Restore
• Pilot Light
• Warm Standby
• Hot Site / Multi Site Approach

# Route53
Simple Records do not have health checks, here the most likely issue is that the TTL is still in effect so you have to wait until it expires for the new users to perform another DNS query and get the value for your new Load Balancer.


# Database

ElastiCache / RDS / Neptune are not serverless databases. DynamoDB is serverless, single digit latency and horizontally scales.

## DynamoDB
DynamoDB Streams will contain a stream of all the changes that happen to a DynamoDB table. It can be chained with a Lambda function that will be triggered to react to these changes, one of which being a developer's milestone. DAX is a caching layer 

## Aurora

Aurora Read Replicas can be deployed globally

# Kinesis


SQS FIFO will not work here as they cannot sustain thousands of messages per second. SNS cannot be used for data streaming. Lambda isn't meant to retain data. Kinesis is the right answer here, with providing a partition key in our message we can guarantee ordering for a specific sensor, even if our stream is sharded


# Q&A

-  Lambda would time out after 15 minutes (2000*3=6000 seconds = 100 minutes). Glue is for performing ETL, but cannot run custom Python scripts. Kinesis Streams is for real time data (here we are in a batch setup), RDS could be used to run SQL queries on the data, but no Python script. The correct answer is EC2
- Elastic Beanstalk cannot manage AWS Lambda functions, OpsWorks is for Chef / Puppet, and Trusted Advisor is to get recommendations regarding the 5 pillars of the well architected framework.
- Kinesis cannot scale infinitely and we may have the same throughput issues. SNS won't keep our data if it cannot be delivered, and DAX is used for caching reads, not to help with writes. Here, using SQS as a middleware will help us sustain the write throughput during write peaks