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

# VPC

you can optionally connect to your own network, known as virtual private clouds (VPCs)

Amazon Web Services. Amazon Elastic Compute Cloud (Kindle Locations 153-154). Amazon Web Services. Kindle Edition. 

Amazon VPC lets you provision a logically isolated section of the Amazon Web Services (AWS) cloud where you can launch AWS resources in a virtual network that you define. You have complete control over your virtual networking environment, including selection of your own IP address ranges, creation of subnets, and configuration of route tables and network gateways. You can also create a hardware Virtual Private Network (VPN) connection between your corporate datacenter and your VPC and leverage the AWS cloud as an extension of your corporate datacenter.

## NACL (Network ACL)
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


# Elastic Load Balancing

To automatically distribute incoming application traffic across multiple instances, use Elastic Load Balancing. 


# Amazon CloudWatch

To monitor basic statistics for your instances and Amazon EBS volumes, use Amazon CloudWatch. 

Amazon Web Services. Amazon Elastic Compute Cloud (Kindle Locations 180-184). Amazon Web Services. Kindle Edition. 

# CloudTrail

To monitor the calls made to the Amazon EC2 API for your account, including calls made by the AWS Management Console, command line tools, and other services, use AWS CloudTrail.

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

## AWS ECS – ECS Setup & Config file
• Run an EC2 instance, install the ECS agent with ECS config file
• Or use an ECS-ready Linux AMI (still need to modify config file) • ECS Config file is at /etc/ecs/ecs.config

## AWS ECR – Elastic Container Registry
• Store, managed and deploy your containers on AWS
• Fully integrated with IAM & ECS
• Sent over HTTPS (encryption in flight) and encrypted at rest