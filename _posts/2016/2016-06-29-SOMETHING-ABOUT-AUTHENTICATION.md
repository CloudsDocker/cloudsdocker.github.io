---
title: Mysql operator to extract JSON
header:
image: /assets/images/Something_about_authentication.jpg
date: 2016-06-29
tags:
- mysql
- database

permalink: /blogs/tech/en/Something_about_authentication
layout: single
category: tech
---
> "Be the change you wish to see in the world." - Mahatma Gandhi

It's annoying to keep on repeating typing same login and password when you access multiple systems within office or for systems in external Internet. There are a bunch of  tools / technical to cater for such. 
To my best knowledge, I'll illustrate some as below.

# SSO (Single Sign On)

After you successfully log into one system,  when you hop onto other systems, so you'll not need to further re-enter your username and password, and you'll in 'logged in status'. 
Under the scene, its sync up your login information among systems. The transferred details is typically called 'tickets'. 
One of the implementation logic is 'kerberos', which is one protocol developed by MIT and is widely used in such domain.
In general, kerberos is supported by various systems and software, for instance, you log onto your Windows desktop, your username and password will be validated in LDAP via either client or API.

Let's go deeper into kerberos process.

## Kerberos in depth.

#### Simple chart
Here is a flow diagram that outlines the Kerberos authentication process:

```shell
               +-------------------------+
               |   Kerberos Authentication   |
               +-------------------------+
                                   |
                          +----------------+
                          |   Client-side   |
                          +----------------+
                                   |
                        +--------------+
                        |   Authenticate  |
                        +--------------+
                                   |
                     +---------------------+
                     |   Request for Ticket   |
                     +---------------------+
                                   |
                 +---------------------------+
                 |   Ticket Granting Service   |
                 +---------------------------+
                                   |
                       +------------+
                       |   Verify   |
                       +------------+
                                   |
               +---------------------------+
               |   Ticket Granting Ticket   |
               +---------------------------+
                                   |
                         +--------------+
                         |   Response   |
                         +--------------+
                                   |
                      +-----------------+
                      |   Service-side   |
                      +-----------------+
                                   |
                        +--------------+
                        |   Authenticate  |
                        +--------------+
                                   |
                    +------------------------+
                    |   Request for Service   |
                    +------------------------+
                                   |
                         +------------+
                         |   Verify   |
                         +------------+
                                   |
                   +------------------------+
                   |   Service Ticket       |
                   +------------------------+
                                   |
                         +------------+
                         |   Response |
                         +------------+

```
### Explanations


 - The client initiates the authentication process by sending a request to the Kerberos Authentication system.
 - The client is authenticated by the Kerberos Authentication system.
 - The client requests a ticket to access a specific service.
 - The Ticket Granting Service (TGS) receives the request and verifies the client's credentials.
 - The TGS issues a Ticket Granting Ticket (TGT) to the client.
 - The client sends the TGT to the service it wishes to access.
 - The service verifies the TGT with the TGS.
 - The service grants a service ticket to the client.
 - The client sends the service ticket to the service it wishes to access.
 - The service verifies the service ticket and grants access to the client.
 - The above diagram shows how Kerberos authentication allows clients to access services on a network in a secure and efficient manner.

## Example of Kerberos

here is an example of how the Kerberos authentication process might work in a real-world scenario:

 1. Alice wants to access a file stored on a server on her company's network.
 1. Alice's computer sends a request to the Kerberos Authentication system, asking for authentication to access the file.
 1. The Kerberos Authentication system authenticates Alice's credentials by verifying her username and password with the company's Active Directory.
 1. Alice's computer requests a ticket to access the file from the Ticket Granting Service (TGS).
 1. The TGS verifies Alice's credentials and issues her a Ticket Granting Ticket (TGT).
 1. Alice's computer sends the TGT to the file server.
 1. The file server verifies the TGT with the TGS.
 1. The file server grants Alice a service ticket to access the file.
 1. Alice's computer sends the service ticket to the file server.
 1. The file server verifies the service ticket and grants Alice access to the file.
In this example, the Kerberos authentication process ensures that Alice can access the file securely and efficiently without having to repeatedly enter her username and password. The process involves several steps, but it all happens automatically behind the scenes, allowing Alice to focus on her work without having to worry about security.

## Implement SSO via kerberos
Kerberos can be used for Single Sign-On (SSO) by allowing users to authenticate themselves once and then use that authentication to access multiple services without having to re-enter their credentials. Here are the steps involved in using Kerberos for SSO:

 1. Users log in to their computer using their network username and password. This initial authentication is typically done through Active Directory or another authentication system.
 1. 
 1. The user's computer sends a request to the Kerberos Authentication system, requesting a Ticket Granting Ticket (TGT).
 1. 
 1. The Kerberos Authentication system verifies the user's credentials with the authentication system (such as Active Directory), and issues a TGT to the user's computer.
 1. 
 1. When the user wants to access a network resource or service, their computer requests a service ticket from the Kerberos Authentication system.
 1. 
 1. The Kerberos Authentication system issues a service ticket to the user's computer.
 1. 
 1. The user's computer sends the service ticket to the resource or service they want to access.
 1. 
 1. The resource or service verifies the service ticket with the Kerberos Authentication system.
 1. 
 1. If the service ticket is valid, the user is granted access to the resource or service.
 1. 
 1. The user can access multiple resources or services on the network without having to re-enter their credentials because their initial authentication is used for all subsequent requests.

Using Kerberos for SSO can simplify the login process for users and reduce the risk of password-related security issues because users don't need to remember or enter their passwords repeatedly. However, it requires a well-configured Kerberos infrastructure and the use of compatible applications and systems that can participate in the Kerberos authentication process.

--HTH--



