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

Permissions let you specify access to AWS resources. Permissions are granted to IAM entities (users, groups, and roles) and by default these entities start with no permissions. In other words, IAM entities can do nothing in AWS until you grant them your desired permissions. To give entities permissions, you can attach a policy that specifies the type of access, the actions that can be performed, and the resources on which the actions can be performed. In addition, you can specify any conditions that must be set for access to be allowed or denied.

## IAM policies
A permissions policy describes who has access to what. Policies attached to an IAM identity are identity-based policies (IAM policies) and policies attached to a resource are resource-based policies. Amazon RDS supports only identity-based policies (IAM policies).


## DB authenticatioin via IAM

MySQL and PostgreSQL both support IAM database authentication.

To protect the confidential data of your customers, you have to ensure that your RDS database can only be accessed using the profile credentials specific to your EC2 instances via an authentication token.   

You can authenticate to your DB instance using AWS Identity and Access Management (IAM) database authentication. IAM database authentication works with MySQL and PostgreSQL. With this authentication method, you don't need to use a password when you connect to a DB instance. Instead, you use an authentication token.

An authentication token is a unique string of characters that Amazon RDS generates on request. Authentication tokens are generated using AWS Signature Version 4. Each token has a lifetime of 15 minutes. You don't need to store user credentials in the database, because authentication is managed externally using IAM. You can also still use standard database authentication.


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


#### EBS snapshot
While it is completing, an in-progress snapshot is not affected by ongoing reads and writes to the volume.

You can take a snapshot of an attached volume that is in use. However, snapshots only capture data that has been written to your Amazon EBS volume at the time the snapshot command is issued. This might exclude any data that has been cached by any applications or the operating system. If you can pause any file writes to the volume long enough to take a snapshot, your snapshot should be complete. However, if you can't pause all file writes to the volume, you should unmount the volume from within the instance, issue the snapshot command, and then remount the volume to ensure a consistent and complete snapshot. You can remount and use your volume while the snapshot status is pending.

#### Save network cost
 S3 would imply changing the application code, Glacier is not applicable as the files are frequently requested, Storage Gateway isn't for distributing files to end users. CloudFront is the right answer, because we can put it in front of our ASG and leverage a Global Caching feature that will help us distribute the content reliably with dramatically reduced costs (the ASG won't need to scale as much)


## EFS
Instance Stores or EBS volumes are local disks and cannot be shared across instances. Here, we need a network file system (NFS), which is exactly what EFS is designed for.


## Redshift
Creating a smaller cluster with the cold data would not decrease the storage cost of Redshift, which will increase as we keep on creating data. Moving the data to S3 glacier will prevent us from being able to query it. Redshift's internal storage does not have "tiers". Therefore, we should migrate the data to S3 IA and use Athena (serverless SQL query engine on top of S3) to analyze the cold data.

# CloundFront

## Origin
Until now, CloudFront could serve up content from Amazon S3. In content-distribution lingo, S3 was the only supported origin server. You would store your web objects (web pages, style sheets, images, JavaScript, and so forth) in S3, and then create a CloudFront distribution. Here is the basic flow:


Effective today we are opening up CloudFront and giving you the ability to use the origin server of your choice.

You can now create a CloudFront distribution using a custom origin. Each distribution will can point to an S3 or to a custom origin. This could be another storage service, or it could be something more interesting and more dynamic, such as an EC2 instance or even an Elastic Load Balancer:


# CloudFormation

## CloudFormation vs Elastic Beanstalk

Elastic Beanstalk provides an environment to easily deploy and run applications in the cloud.
CloudFormation is a convenient provisioning mechanism for a broad range of AWS resources.


# VPC
you can optionally connect to your own network, known as virtual private clouds (VPCs)

Amazon Web Services. Amazon Elastic Compute Cloud (Kindle Locations 153-154). Amazon Web Services. Kindle Edition. 

Amazon VPC lets you provision a logically isolated section of the Amazon Web Services (AWS) cloud where you can launch AWS resources in a virtual network that you define. You have complete control over your virtual networking environment, including selection of your own IP address ranges, creation of subnets, and configuration of route tables and network gateways. You can also create a hardware Virtual Private Network (VPN) connection between your corporate datacenter and your VPC and leverage the AWS cloud as an extension of your corporate datacenter.

## Subnet
A subnet is a range of IP addresses in your VPC. You can launch AWS resources into a specified subnet. Use a public subnet for resources that must be connected to the internet, and a private subnet for resources that won’t be connected to the internet.
To protect the AWS resources in each subnet, use security groups and network access control lists (ACL).

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

## How to prevent DDoS
AWS provides flexible infrastructure and services that help customers implement strong DDoS mitigations and create highly available application architectures that follow AWS Best Practices for DDoS Resiliency. These include services such as Amazon Route 53, Amazon CloudFront, Elastic Load Balancing, and AWS WAF to control and absorb traffic, and deflect unwanted requests. These services integrate with AWS Shield, a managed DDoS protection service that provides always-on detection and automatic inline mitigations to safeguard web applications running on AWS.

### AWS Shield

AWS Shield is a managed DDoS protection service that is available in two tiers: Standard and Advanced. AWS Shield Standard applies always-on detection and inline mitigation techniques, such as deterministic packet filtering and priority-based traffic shaping, to minimize application downtime and latency. 

#### AWS Shield Standard 
It is included automatically and transparently to your Elastic Load Balancing load balancers, Amazon CloudFront distributions, and Amazon Route 53 resources at no additional cost. When you use these services that include AWS Shield Standard, you receive comprehensive availability protection against all known infrastructure layer attacks. Customers who have the technical expertise to manage their own monitoring and mitigation of application layer attacks can use AWS Shield together with AWS WAF rules to create a comprehensive DDoS attack mitigation strategy.

#### AWS Shield Advanced 
It provides enhanced DDoS attack detection and monitoring for application-layer traffic to your Elastic Load Balancing load balancers, CloudFront distributions, Amazon Route 53 hosted zones and resources attached to an Elastic IP address, such Amazon EC2 instances. AWS Shield Advanced uses additional techniques to provide granular detection of DDoS attacks, such as resource-specific traffic monitoring to detect HTTP floods or DNS query floods. AWS Shield Advanced includes 24x7 access to the AWS DDoS Response Team (DRT), support experts who apply manual mitigations for more complex and sophisticated DDoS attacks, directly create or update AWS WAF rules, and can recommend improvements to your AWS architectures. AWS WAF is included at no additional cost for resources that you protect with AWS Shield Advanced.

AWS Shield Advanced includes access to near real-time metrics and reports, for extensive visibility into infrastructure layer and application layer DDoS attacks. You can combine AWS Shield Advanced metrics with additional, fine-tuned AWS WAF metrics for a more comprehensive CloudWatch monitoring and alarming strategy. Customers subscribed to AWS Shield Advanced can also apply for a credit for charges that result from scaling during a DDoS attack on protected Amazon EC2, Amazon CloudFront, Elastic Load Balancing, or Amazon Route 53 resources. See the AWS Shield Developer Guide for a detailed comparison of the two AWS Shield offerings.


## CIDR
To add a CIDR block to your VPC, the following rules apply:

-The allowed block size is between a /28 netmask and /16 netmask.
-The CIDR block must not overlap with any existing CIDR block that's associated with the VPC.
-You cannot increase or decrease the size of an existing CIDR block.
-You have a limit on the number of CIDR blocks you can associate with a VPC and the number of routes you can add to a route table. You cannot associate a CIDR block if this results in you exceeding your limits.
-The CIDR block must not be the same or larger than the CIDR range of a route in any of the VPC route tables. For example, if you have a route with a destination of 10.0.0.0/24 to a virtual private gateway, you cannot associate a CIDR block of the same range or larger. However, you can associate a CIDR block of 10.0.0.0/25 or smaller.
-The first four IP addresses and the last IP address in each subnet CIDR block are not available for you to use, and cannot be assigned to an instance.


# AWS WAF

AWS WAF is a web application firewall that helps protect web applications from common web exploits that could affect application availability, compromise security, or consume excessive resources. You can use AWS WAF to define customizable web security rules that control which traffic accesses your web applications. If you use AWS Shield Advanced, you can use AWS WAF at no extra cost for those protected resources and can engage the DRT to create WAF rules.

AWS WAF rules use conditions to target specific requests and trigger an action, allowing you to identify and block common DDoS request patterns and effectively mitigate a DDoS attack. These include size constraint conditions to block a web request based on the length of its query string or request body, and geographic match conditions to implement geo restriction (also known as geoblocking) on requests that originate from specific countries. 

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


## Amazon RDS Multi-AZ Deployments
Amazon RDS Multi-AZ deployments provide enhanced availability and durability for Database (DB) Instances, making them a natural fit for production database workloads. When you provision a Multi-AZ DB Instance, Amazon RDS automatically creates a primary DB Instance and synchronously replicates the data to a standby instance in a different Availability Zone (AZ). Each AZ runs on its own physically distinct, independent infrastructure, and is engineered to be highly reliable. In case of an infrastructure failure, Amazon RDS performs an automatic failover to the standby (or to a read replica in the case of Amazon Aurora), so that you can resume database operations as soon as the failover is complete. Since the endpoint for your DB Instance remains the same after a failover, your application can resume database operation without the need for manual administrative intervention.


## Security
Use security groups to control what IP addresses or Amazon EC2 instances can connect to your databases on a DB instance.
Run your DB instance in an Amazon Virtual Private Cloud (VPC) for the greatest possible network access control.

## Working with a DB Instance in a VPC
Your VPC must have at least two subnets. These subnets must be in two different Availability Zones in the region where you want to deploy your DB instance.
If you want your DB instance in the VPC to be publicly accessible, you must enable the VPC attributes DNS hostnames and DNS resolution.

# Elastic Cache
IAM Auth is not supported by ElastiCache

# Amazon CloudWatch

To monitor basic statistics for your instances and Amazon EBS volumes, use Amazon CloudWatch. 

Amazon Web Services. Amazon Elastic Compute Cloud (Kindle Locations 180-184). Amazon Web Services. Kindle Edition. 

Disabling the Termination from the ASG would prevent our ASG to be Elastic and impact our costs. Making a snapshot of the EC2 instance before it gets terminated *could* work but it's tedious, not elastic and very expensive, as all we're interested about are log files. Using AWS Lambda would be extremely hard to use for this task. Here, the natural and by far easiest solution would be to use the CloudWatch Logs agents on the EC2 instances to automatically send log files into CloudWatch, so we can analyze them in the future easily should any problems arise.

# API Gateway
Q: What API types are supported by Amazon API Gateway?

Amazon API Gateway offers two options to create RESTful APIs, HTTP APIs (Preview) and REST APIs, as well as an option to create WebSocket APIs.

HTTP API: HTTP APIs, currently available in Preview, are optimized for building APIs that proxy to AWS Lambda functions or HTTP backends, making them ideal for serverless workloads. They do not currently offer API management functionality.

REST API: REST APIs offer API proxy functionality and API management features in a single solution. REST APIs offer API management features such as usage plans, API keys, publishing, and monetizing APIs.

WebSocket API: WebSocket APIs maintain a persistent connection between connected clients to enable real-time message communication. With WebSocket APIs in API Gateway, you can define backend integrations with AWS Lambda functions, Amazon Kinesis, or any HTTP endpoint to be invoked when messages are received from the connected clients.

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

## Specifying Sensitive Data
Amazon ECS enables you to inject sensitive data into your containers by storing your sensitive data in either AWS Secrets Manager secrets or AWS Systems Manager Parameter Store parameters and then referencing them in your container definition. This feature is supported by tasks using both the EC2 and Fargate launch types.

### Required IAM Permissions for Amazon ECS Secrets

To use this feature, you must have the Amazon ECS task execution role and reference it in your task definition. This allows the container agent to pull the necessary AWS Systems Manager or Secrets Manager resources. For more information, see Amazon ECS Task Execution IAM Role.

To provide access to the AWS Systems Manager Parameter Store parameters that you create, manually add the following permissions as an inline policy to the task execution role. For more information, see Adding and Removing IAM Policies.

ssm:GetParameters—Required if you are referencing a Systems Manager Parameter Store parameter in a task definition.

secretsmanager:GetSecretValue—Required if you are referencing a Secrets Manager secret either directly or if your Systems Manager Parameter Store parameter is referencing a Secrets Manager secret in a task definition.

kms:Decrypt—Required only if your secret uses a custom KMS key and not the default key. The ARN for your custom key should be added as a resource.

# Lambda
AWS Lambda functions time out after 15 minutes, and are not usually meant for long running jobs.

## Lambda parameters Encryption
Although Lambda encrypts the environment variables in your function by default, the sensitive information would still be visible to other users who have access to the Lambda console. This is because Lambda uses a default KMS key to encrypt the variables, which is usually accessible by other users. The best option in this scenario is to use encryption helpers to secure your environment variables.

Enabling SSL would encrypt data only when in-transit. Your other teams would still be able to view the plaintext at-rest. Use AWS KMS instead.

Option 3 is incorrect since, as mentioned, Lambda does provide encryption functionality of environment variables.	
## Lambda functions
You upload your application code in the form of one or more Lambda functions. Lambda stores code in Amazon S3 and encrypts it at rest.
###  layer 
A layer is a ZIP archive that contains libraries, a custom runtime, or other dependencies. Use layers to manage your function’s dependencies independently and keep your deployment package small.

### Invoking Functions

Lambda supports synchronous and asynchronous invocation of a Lambda function. You can control the invocation type only when you invoke a Lambda function (referred to as on-demand invocation).
An event source is the entity that publishes events, and a Lambda function is the custom code that processes the events.
Event source mapping maps an event source to a Lambda function. It enables automatic invocation of your Lambda function when events occur.

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

## DynamoDB's partition key

DynamoDB supports two types of primary keys:

Partition key: A simple primary key, composed of one attribute known as the partition key. Attributes in DynamoDB are similar in many ways to fields or columns in other database systems.
Partition key and sort key: Referred to as a composite primary key, this type of key is composed of two attributes. The first attribute is the partition key, and the second attribute is the sort key. Following is an example.

### Recommendations for partition keys

Use high-cardinality attributes. These are attributes that have distinct values for each item, like e-mailid, employee_no, customerid, sessionid, orderid, and so on.

Use composite attributes. Try to combine more than one attribute to form a unique key, if that meets your access pattern. For example, consider an orders table with customerid+productid+countrycode as the partition key and order_date as the sort key.

Cache the popular items when there is a high volume of read traffic using Amazon DynamoDB Accelerator (DAX). The cache acts as a low-pass filter, preventing reads of unusually popular items from swamping partitions. For example, consider a table that has deals information for products. Some deals are expected to be more popular than others during major sale events like Black Friday or Cyber Monday. DAX is a fully managed, in-memory cache for DynamoDB that doesn’t require developers to manage cache invalidation, data population, or cluster management. DAX also is compatible with DynamoDB API calls, so developers can incorporate it more easily into existing applications.

Add random numbers or digits from a predetermined range for write-heavy use cases. Suppose that you expect a large volume of writes for a partition key (for example, greater than 1000 1 K writes per second). In this case, use an additional prefix or suffix (a fixed number from predetermined range, say 1–10) and add it to the partition key.


## Aurora

Aurora Read Replicas can be deployed globally

### Aurora endpoints
Amazon Aurora typically involves a cluster of DB instances instead of a single instance. Each connection is handled by a specific DB instance. When you connect to an Aurora cluster, the host name and port that you specify point to an intermediate handler called an endpoint. Aurora uses the endpoint mechanism to abstract these connections. Thus, you don't have to hardcode all the hostnames or write your own logic for load-balancing and rerouting connections when some DB instances aren't available.

For certain Aurora tasks, different instances or groups of instances perform different roles. For example, the primary instance handles all data definition language (DDL) and data manipulation language (DML) statements. Up to 15 Aurora Replicas handle read-only query traffic.

Using endpoints, you can map each connection to the appropriate instance or group of instances based on your use case. For example, to perform DDL statements you can connect to whichever instance is the primary instance. To perform queries, you can connect to the reader endpoint, with Aurora automatically performing load-balancing among all the Aurora Replicas. For clusters with DB instances of different capacities or configurations, you can connect to custom endpoints associated with different subsets of DB instances. For diagnosis or tuning, you can connect to a specific instance endpoint to examine details about a specific DB instance.


#### Types of Aurora Endpoints

An endpoint is represented as an Aurora-specific URL that contains a host address and a port. The following types of endpoints are available from an Aurora DB cluster.

##### Cluster endpoint
A cluster endpoint for an Aurora DB cluster that connects to the current primary DB instance for that DB cluster. This endpoint is the only one that can perform write operations such as DDL statements. Because of this, the cluster endpoint is the one that you connect to when you first set up a cluster or when your cluster only contains a single DB instance.
Each Aurora DB cluster has one cluster endpoint and one primary DB instance.

You use the cluster endpoint for all write operations on the DB cluster, including inserts, updates, deletes, and DDL changes. You can also use the cluster endpoint for read operations, such as queries.

The cluster endpoint provides failover support for read/write connections to the DB cluster. If the current primary DB instance of a DB cluster fails, Aurora automatically fails over to a new primary DB instance. During a failover, the DB cluster continues to serve connection requests to the cluster endpoint from the new primary DB instance, with minimal interruption of service.

##### Reader endpoint
A reader endpoint for an Aurora DB cluster connects to one of the available Aurora Replicas for that DB cluster. Each Aurora DB cluster has one reader endpoint. If there is more than one Aurora Replica, the reader endpoint directs each connection request to one of the Aurora Replicas.

The reader endpoint provides load-balancing support for read-only connections to the DB cluster. Use the reader endpoint for read operations, such as queries. You can't use the reader endpoint for write operations.

##### Custom endpoint
A custom endpoint for an Aurora cluster represents a set of DB instances that you choose. When you connect to the endpoint, Aurora performs load balancing and chooses one of the instances in the group to handle the connection. You define which instances this endpoint refers to, and you decide what purpose the endpoint serves.

An Aurora DB cluster has no custom endpoints until you create one. You can create up to five custom endpoints for each provisioned Aurora cluster. You can't use custom endpoints for Aurora Serverless clusters.

The custom endpoint provides load-balanced database connections based on criteria other than the read-only or read-write capability of the DB instances. For example, you might define a custom endpoint to connect to instances that use a particular AWS instance class or a particular DB parameter group. Then you might tell particular groups of users about this custom endpoint. For example, you might direct internal users to low-capacity instances for report generation or ad hoc (one-time) querying, and direct production traffic to high-capacity instances.

Instead of using one DB instance for each specialized purpose and connecting to its instance endpoint, you can have multiple groups of specialized DB instances. In this case, each group has its own custom endpoint. This way, Aurora can perform load balancing among all the instances dedicated to tasks such as reporting or handling production or internal queries. The custom endpoints provide load balancing and high availability for each group of DB instances within your cluster. If one of the DB instances within a group becomes unavailable, Aurora directs subsequent custom endpoint connections to one of the other DB instances associated with the same endpoint.

##### Instance endpoint
An instance endpoint connects to a specific DB instance within an Aurora cluster. Each DB instance in a DB cluster has its own unique instance endpoint. So there is one instance endpoint for the current primary DB instance of the DB cluster, and there is one instance endpoint for each of the Aurora Replicas in the DB cluster.

The instance endpoint provides direct control over connections to the DB cluster, for scenarios where using the cluster endpoint or reader endpoint might not be appropriate. For example, your client application might require more fine-grained load balancing based on workload type. In this case, you can configure multiple clients to connect to different Aurora Replicas in a DB cluster to distribute read workloads. 


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


# ElasticCache

## Redis

### What are Amazon ElastiCache for Redis nodes, clusters, and replications groups?

An ElastiCache for Redis node is the smallest building block of an Amazon ElastiCache for Redis deployment. Each ElastiCache for Redis node supports the Redis protocol and has its own DNS name and port. Multiple types of ElastiCache for Redis nodes are supported, each with varying amount of CPU capability, and associated memory. An ElastiCache for Redis node may take on a primary or a read replica role. A primary node can be replicated to multiple read replica nodes. An ElastiCache for Redis cluster is a collection of one or more ElastiCache for Redis nodes of the same role; the primary node will be in the primary cluster and the read replica node will be in a read replica cluster. At this time a cluster can only have one node. In the future, we will increase this limit. A cluster manages a logical key space, where each node is responsible for a part of the key space. Most of your management operations will be performed at the cluster level. An ElastiCache for Redis replication group encapsulates the primary and read replica clusters for a Redis installation. A replication group will have only one primary cluster and zero or many read replica clusters. All nodes within a replication group (and consequently cluster) will be of the same node type, and have the same parameter and security group settings.

### Does Amazon ElastiCache for Redis support Multi-AZ operation?

Yes, with Amazon ElastiCache for Redis you can create a read replica in another AWS Availability Zone. Upon a failure of the primary node, we will provision a new primary node. In scenarios where the primary node cannot be provisioned, you can decide which read replica to promote to be the new primary. 

### What is Multi-AZ for an ElastiCache for Redis replication group?

An ElastiCache for Redis replication group consists of a primary and up to five read replicas. Redis asynchronously replicates the data from the primary to the read replicas. During certain types of planned maintenance, or in the unlikely event of ElastiCache node failure or Availability Zone failure, Amazon ElastiCache will automatically detect the failure of a primary, select a read replica, and promote it to become the new primary. ElastiCache also propagates the DNS changes of the promoted read replica, so if your application is writing to the primary node endpoint, no endpoint change will be needed.

### How can I use encryption in-transit, at-rest, and Redis AUTH?

Encryption in-transit, encryption at-rest, and Redis AUTH are all opt-in features. At the time of Redis cluster creation via the console or command line interface, you can specify if you want to enable encryption and Redis AUTH and can proceed to provide an authentication token for communication with the Redis cluster. Once the cluster is setup with encryption enabled, ElastiCache seamlessly manages certificate expiration and renewal without requiring any additional action from the application. Additionally, the Redis clients need to support TLS to avail of the encrypted in-transit traffic.

### Is Redis password functionality supported in Amazon ElastiCache for Redis?

Yes, Amazon ElastiCache for Redis supports Redis passwords via Redis AUTH feature. It is an opt-in feature available in ElastiCache for Redis version 3.2.6 onwards. You must enable encryption in-transit to use Redis AUTH on your ElastiCache for Redis cluster.

### encryption
ElastiCache for Redis at-rest encryption is an optional feature to increase data security by encrypting on-disk data. When enabled on a replication group, it encrypts the following aspects:

Disk during sync, backup and swap operations

Backups stored in Amazon S3

ElastiCache for Redis offers default (service managed) encryption at rest, as well as ability to use your own symetric customer managed customer master keys in AWS Key Management Service (KMS).

#### KMS
Manage keys used for encrypted DB instances using the AWS KMS. KMS encryption keys are specific to the region that they are created in.

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


# Resources
- RDS cheatsheet: https://tutorialsdojo.com/aws-cheat-sheet-amazon-relational-database-service-amazon-rds/
- VPC cheatsheet: https://tutorialsdojo.com/aws-cheat-sheet-amazon-vpc/