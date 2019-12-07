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


 When you launch a new EC2 instance, the EC2 service attempts to place the instance in such a way that all of your instances are spread out across underlying hardware to minimize correlated failures. You can use placement groups to influence the placement of a group of interdependent instances to meet the needs of your workload. Depending on the type of workload, you can create a placement group using one of the following placement strategies:

 Cluster – packs instances close together inside an Availability Zone. This strategy enables workloads to achieve the low-latency network performance necessary for tightly-coupled node-to-node communication that is typical of HPC applications.

 Partition – spreads your instances across logical partitions such that groups of instances in one partition do not share the underlying hardware with groups of instances in different partitions. This strategy is typically used by large distributed and replicated workloads, such as Hadoop, Cassandra, and Kafka.

 Spread – strictly places a small group of instances across distinct underlying hardware to reduce correlated failures.

 There is no charge for creating a placement group.

### Cluster

 Cluster Placement Groups

A cluster placement group is a logical grouping of instances within a single Availability Zone. A placement group can span peered VPCs in the same Region. The chief benefit of a cluster placement group, in addition to a 10 Gbps flow limit, is the non-blocking, non-oversubscribed, fully bi-sectional nature of the connectivity. In other words, all nodes within the placement group can talk to all other nodes within the placement group at the full line rate of 10 Gbps flows and 100 Gbps aggregate without any slowing due to over-subscription.

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

## STS
Temporary Security Credentials
You can use the AWS Security Token Service (AWS STS) to create and provide trusted users with temporary security credentials that can control access to your AWS resources. Temporary security credentials work almost identically to the long-term access key credentials that your IAM users can use, with the following differences:

Temporary security credentials are short-term, as the name implies. They can be configured to last for anywhere from a few minutes to several hours. After the credentials expire, AWS no longer recognizes them or allows any kind of access from API requests made with them.

Temporary security credentials are not stored with the user but are generated dynamically and provided to the user when requested. When (or even before) the temporary security credentials expire, the user can request new credentials, as long as the user requesting them still has permissions to do so.


# Storage
### Performance
Instance Store will have the highest disk performance but comes with the storage being wiped if the instance is terminated, which is acceptable in this case. EBS volumes would provide good performance as far as disk goes, but not as good as Instance Store. EBS data survives instance termination or reboots. EFS is a network drive, and finally S3 cannot be mounted as a local disk (natively).

Need to define two terms:
• RPO: Recovery Point Objective
• RTO: Recovery Time Objective

## S3
Generating S3 pre-signed URLs would bypass CloudFront, therefore we should use CloudFront signed URL. To generate that URL we must code, and Lambda is the perfect tool for running that code on the fly. 

As the file is greater than 5GB in size, you must use Multi Part upload to upload that file to S3.

### OAI
Don't make the S3 bucket public. You cannot attach IAM roles to the CloudFront distribution. S3 buckets don't have security groups. Here you need to use an OAI. Read more here: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

Restricting Access to Amazon S3 Content by Using an Origin Access Identity
To restrict access to content that you serve from Amazon S3 buckets, you create CloudFront signed URLs or signed cookies to limit access to files in your Amazon S3 bucket, and then you create a special CloudFront user called an origin access identity (OAI) and associate it with your distribution. Then you configure permissions so that CloudFront can use the OAI to access and serve files to your users, but users can't use a direct URL to the S3 bucket to access a file there. Taking these steps help you maintain secure access to the files that you serve through CloudFront.

In general, if you're using an Amazon S3 bucket as the origin for a CloudFront distribution, you can either allow everyone to have access to the files there, or you can restrict access. If you limit access by using, for example, CloudFront signed URLs or signed cookies, you also won't want people to be able to view files by simply using the direct URL for the file. Instead, you want them to only access the files by using the CloudFront URL, so your protections work. For more information about using signed URLs and signed cookies, see Serving Private Content with Signed URLs and Signed Cookies

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


You can now choose between three Amazon EBS volume types to best meet the needs of your workloads: General Purpose (SSD), Provisioned IOPS (SSD), and Magnetic volumes. 

#### General Purpose (SSD) 
GP2 volumes are suitable for a broad range of workloads, including small to medium-sized databases, development and test environments, and boot volumes. 
#### Provisioned IOPS (SSD) 
Such volumes offer storage with consistent and low-latency performance, are designed for I/O-intensive applications such as large relational or NoSQL databases, and allow you to choose the level of performance you need. 
#### Magnetic volumes
formerly known as Standard volumes, provide the lowest cost per gigabyte of all Amazon EBS volume types and are ideal for workloads where data is accessed infrequently and applications where the lowest storage cost is important.



Backed by Solid-State Drives (SSDs), General Purpose (SSD) volumes provide the ability to burst to 3,000 IOPS per volume, independent of volume size, to meet the performance needs of most applications and also deliver a consistent baseline of 3 IOPS/GB. General Purpose (SSD) volumes offer the same five nines of availability and durable snapshot capabilities as other volume types. Pricing and performance for General Purpose (SSD) volumes are simple and predictable. You pay for each GB of storage you provision, and there are no additional charges for I/O performed on a volume. Prices start as low as $0.10/GB.


#### Save network cost
 S3 would imply changing the application code, Glacier is not applicable as the files are frequently requested, Storage Gateway isn't for distributing files to end users. CloudFront is the right answer, because we can put it in front of our ASG and leverage a Global Caching feature that will help us distribute the content reliably with dramatically reduced costs (the ASG won't need to scale as much)


## EFS
Instance Stores or EBS volumes are local disks and cannot be shared across instances. Here, we need a network file system (NFS), which is exactly what EFS is designed for.


## Redshift
Creating a smaller cluster with the cold data would not decrease the storage cost of Redshift, which will increase as we keep on creating data. Moving the data to S3 glacier will prevent us from being able to query it. Redshift's internal storage does not have "tiers". Therefore, we should migrate the data to S3 IA and use Athena (serverless SQL query engine on top of S3) to analyze the cold data.


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

### IGW (Internet GateWay)
After creating an IGW, make sure the route tables are updated. Additionally, ensure the security group allow the ICMP protocol for ping requests


### NAT
NAT Instances would work but won't scale and you would have to manage them (as they're EC2 instances). Egress-Only Internet Gateways are for IPv6, not IPv4. Internet Gateways must be deployed in a public subnet. Therefore you must use a NAT Gateway in your public subnet in order to provide internet access to your instances in your private subnets.

# AWS SSM (Simple System Manager)

AWS SSM is parameter store.

# ELB: Elastic Load Balancing

To automatically distribute incoming application traffic across multiple instances, use Elastic Load Balancing. 

For HA, even though our ASG is deployed across 3 AZ, the minimum capacity to be highly available is 2. Finally, we can save costs by reserving these two instances as we know they'll be up and running at any time

## Application Load Balancer vs Network load balancer
Path based routing and host based routing are only available for the Application Load Balancer (ALB). Deploying an NGINX load balancer on EC2 would work but would suffer management and scaling issues. Read more here: https://aws.amazon.com/blogs/aws/new-host-based-routing-support-for-aws-application-load-balancers/

### ALB & ASG
Adding the entire CIDR of the ALB would work, but wouldn't guarantee that only the ALB can access the EC2 instances that are part of the ASG. Here, the right solution is to add a rule on the ASG security group to allow incoming traffic from the security group configured for the ALB.

### SNI
support for multiple TLS/SSL certificates on Application Load Balancers (ALB) using Server Name Indication (SNI). You can now host multiple TLS secured applications, each with its own TLS certificate, behind a single load balancer. In order to use SNI, all you need to do is bind multiple certificates to the same secure listener on your load balancer. ALB will automatically choose the optimal TLS certificate for each client. These new features are provided at no additional charge.

One of our most frequent requests on forums, reddit, and in my e-mail inbox has been to use the Server Name Indication (SNI) extension of TLS to choose a certificate for a client. Since TLS operates at the transport layer, below HTTP, it doesn’t see the hostname requested by a client. SNI works by having the client tell the server “This is the domain I expect to get a certificate for” when it first connects. The server can then choose the correct certificate to respond to the client. All modern web browsers and a large majority of other clients support SNI. In fact, today we see SNI supported by over 99.5% of clients connecting to CloudFront.


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

Disabling the Termination from the ASG would prevent our ASG to be Elastic and impact our costs. Making a snapshot of the EC2 instance before it gets terminated *could* work but it's tedious, not elastic and very expensive, as all we're interested about are log files. Using AWS Lambda would be extremely hard to use for this task. Here, the natural and by far easiest solution would be to use the CloudWatch Logs agents on the EC2 instances to automatically send log files into CloudWatch, so we can analyze them in the future easily should any problems arise.


# CloudTrail

To monitor the calls made to the Amazon EC2 API for your account, including calls made by the AWS Management Console, command line tools, and other services, use AWS CloudTrail.

In general, to analyze any API calls made within your AWS account, you should use CloudTrail


​
Set up a new CloudTrail trail in a new S3 bucket using the AWS CLI and also pass both the --is-multi-region-trail and --include-global-service-events parameters then encrypt log files using KMS encryption. Apply Multi Factor Authentication (MFA) Delete on the S3 bucket and ensure that only authorized users can access the logs by configuring the bucket policies.


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

### DAX
DAX will be transparent and won't require an application refactoring, and will cache the "hot keys". ElastiCache could also be a solution, but it will require a lot of refactoring work on the AWS Lambda side.

DynamoDB is horizontally scalable, has a DynamoDB streams capability and is multi AZ by default. On top of it, we can adjust the RCU and WCU automatically using Auto Scaling.

## Aurora

Aurora Read Replicas can be deployed globally

# Kinesis


SQS FIFO will not work here as they cannot sustain thousands of messages per second. SNS cannot be used for data streaming. Lambda isn't meant to retain data. Kinesis is the right answer here, with providing a partition key in our message we can guarantee ordering for a specific sensor, even if our stream is sharded


# BeanStalk
When you create an AWS Elastic Beanstalk environment, you can specify an Amazon Machine Image (AMI) to use instead of the standard Elastic Beanstalk AMI included in your platform version. A custom AMI can improve provisioning times when instances are launched in your environment if you need to install a lot of software that isn't included in the standard AMIs. Read more here: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features.customenv.html

# MQ
SNS, SQS and Kinesis are AWS' proprietary technologies and do not come with MQTT compatibility. Here the only possible answer is Amazon MQ

# X Ray
 AWS X-Ray
Analyze and debug production, distributed applications

AWS X-Ray helps developers analyze and debug production, distributed applications, such as those built using a microservices architecture. With X-Ray, you can understand how your application and its underlying services are performing to identify and troubleshoot the root cause of performance issues and errors. X-Ray provides an end-to-end view of requests as they travel through your application, and shows a map of your application’s underlying components. You can use X-Ray to analyze both applications in development and in production, from simple three-tier applications to complex microservices applications consisting of thousands of services.



# Q&A

-  Lambda would time out after 15 minutes (2000*3=6000 seconds = 100 minutes). Glue is for performing ETL, but cannot run custom Python scripts. Kinesis Streams is for real time data (here we are in a batch setup), RDS could be used to run SQL queries on the data, but no Python script. The correct answer is EC2
- Elastic Beanstalk cannot manage AWS Lambda functions, OpsWorks is for Chef / Puppet, and Trusted Advisor is to get recommendations regarding the 5 pillars of the well architected framework.
- Kinesis cannot scale infinitely and we may have the same throughput issues. SNS won't keep our data if it cannot be delivered, and DAX is used for caching reads, not to help with writes. Here, using SQS as a middleware will help us sustain the write throughput during write peaks
- CloudFront is not a good solution here as the content is highly dynamic, and CloudFront will cache things. Dynamic applications cannot be deployed to S3, and Route53 does not help in scaling your application. ASG is the correct answer here
- Network Load Balancers expose a fixed IP to the public web, therefore allowing your application to be predictably reached using these IPs, while allowing you to scale your application behind the Network Load Balancer using an ASG. Application and Classic Load Balancers expose a fixed DNS (=URL). Finally, the ASG does not have a dynamic Elastic IPs attachment feature
- Hosting the master pack into S3 will require an application code refactor. Upgrading the EC2 instances won't help save network cost and ELB does not have any caching capability. Here you need to create a CloudFront distribution to add a caching layer in front of your ELB. That caching layer will be very effective as the image pack is a static file, and tremendously save in network cost.
- Adding Aurora Read Replicas would greatly increase the cost, switching to a Load Balancer would not improve the problems, and AWS Lambda has no native in memory caching capability. Here, using API Gateway Caching feature is the answer, as we can accept to serve stale data to our users
- SQS will allow you to buffer the image compression requests and process them asynchronously. It also has a direct built-in mechanism for retries and scales seamlessly. To process these jobs, due to the unpredictable nature of their volume, and the desire to save on costs, Spot Instances are recommended.
- Distributing the static content through S3 allows to offload most of the network usage to S3 and free up our applications running on ECS. EFS will not change anything as static content on EFS would still have to be distributed by our ECS instances
- S3 does not work as overwrites are eventually consistent so the latest data will not always be read. Neptune is a graph database so it's not a good fit, ElastiCache could work but it's a better fit as a caching technology to enhance reads. Here, the best fit is RDS.
- RDS Multi AZ helps with disaster recovery in case of an AZ failure. ElastiCache would definitely help with the read load, but would require a refactor of the application's core logic. DynamoDB with DAX would also probably help with the read load, but once again it would require a refactor of the application's core logic. Here, our only option to scale reads is to use RDS Read Replicas