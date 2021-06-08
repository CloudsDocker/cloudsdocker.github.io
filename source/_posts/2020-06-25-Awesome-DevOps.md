---
title: DevOps In a nutshell
tags:
- DevOps
---

*Confuse of Dev or Ops? Simple rule: if you are praise for Web site success, you
are Dev; if you are blame when Web site down, you are Ops.*

—DevOps Borat1

*Survey is show junior devops are still believe in Tooth Fairy, Santa Claus and
documentation.*

—DevOps Borat1

*You can only able call yourself senior programmer if you are spend more
minute in meeting as in write code.*

—DevOps Borat1

*48% of devops are automate their test. 12% are test their automation. 3% are
do both.*

—DevOps Borat1

*In Agile is all about fail quick. If you have success in company you do Agile
wrong.*

—DevOps Borat1

## Sharing

Sharing is not just knowledge but also 'scripts'

Sharing the scripts in the version control system enables all parties, particularly development and operations, to use those scripts to set up their respective environments: test environments (used by development) and production environments (managed by operations).

Development and operations work hand in hand, with shared goals, processes, and tools.

**Automation is an essential backbone of DevOps** (see Chapter 3 and Chapter 8 for more information on automation). Automation is the use of solutions to reduce the need for human work.

In software development projects, a high level of automation is a prerequisite for **quickly delivering the best quality** and for obtaining **feedback from stakeholders early and often.**

**Rewarding everyone for stable innovations fosters collaboration**. As a prerequisite, t*eams are cross-functional*. The team includes programmers, testers, QA, and operations. Thus, individual experts *share their skills and experiences with others*, which leads to a one team approach where individuals have at least a basic understanding of others’ domains

Because of this resistance, the incentives and **commitment provided by upper management are important**.

In the past, Agile approaches successfully addressed common obstacles between programmers, testers, QA, and customers, but conflicts still remained. We’ve identified the conflicts between development and operations that have often led to silos and suboptimal solutions. The blame game between development and operations often occurs, which shows the conflicts produced by divergent goals, processes, and tools.

In a nutshell, the conflict between development and operations is as follows:

- *Need for change*: Development produces changes (e.g., new features,
bug fixes, and work based on change requests). They want their
changes rolled out to production.
- *Fear of change*: Once the software is delivered, the operations
department wants to avoid making changes to the software to ensure
stable conditions for the production systems.

DevOps encompasses numerous activities and aspects, such as the following2:

- *Culture*: People over processes and tools. Software is made by and for

    people.

- ***Automation*: Automation is essential for DevOps to gain quick**
feedback.
- *Measurement*: DevOps finds a specific path to measurement. *Quality
and shared (or at least aligned) incentives are critical*.
- ***Sharing***: Creates a culture where people share ideas, processes, and
tools.

If a service goes down, everyone must know what procedures to follow to diagnose the problem and get the system up and running again. Additionally, all of the roles and skills necessary to perform these tasks must be available and able to work together well. **Training and effective collaboration are critical here**.

## Tools

**Processes are more important than tools**, but tools are still important, especially for automating
activities along the delivery process. **The more tools you have in your tool kit, the better you can
decide which tool is the best fit for a given task**.

- Including development and operations in a comprehensive end-to-
end delivery process.
- Including operations in Agile frameworks and processes, such as
Scrum and Kanban.

    Development and operations share the same processes, and both groups are focused on
    delivering application changes to the user at a high frequency and quality. The unified process
    emphasizes the cycle time and prefers the vertical optimization approach.

Steve Jobs used to say, “Real artists ship.”

I'm a senior manager for the DevOps team here. I also have site reliability engineers. So our daily job is to automate and make life better.

**Projects often go through the following phases:**

*Inception*: In this interval, the vision of the system is developed, a
project scope is defined, and the business case is justified.

*Elaboration*: In this interval, requirements are gathered and defined,
risk factors are identified, and a system architecture is initialized.

*Construction*: In this interval, the software is constructed,
programmed, and tested.

*Transition*: In this interval, the software is delivered to the user.
*Operations*: In this interval, the software is available to the user and is

maintained by the operations team.

Agile software development spans the process from inception to transition. DevOps spans the process from elaboration to operations, and often includes departments such as HR and finance

DevOps respects the fact that companies and projects have specific cultures and that people are more important than processes, which, in turn, are more important than tools. DevOps accepts the inevitability of conflicts between development and operations.

For example, DevOps does not grant developers permission to work on production systems. Instead, DevOps is about discipline, conventions, and a defined process that is transparent for all.

There is **no one-size-fits-all solution, and no “DevOps-by-the-book” approach will solve all of your problems**.

From another perspec- tive, DevOps aims to extend Agile to operations.

Development strives for change (e.g., new features and bug fixes), whereas the operations team strives for stability. Often, those groups are paid precisely for these tasks: development obtains bonus pay- ments if the software is delivered, whereas operations is rewarded if production systems are stable. Thus, the development department desires a high flow of newly provided functionality, whereas the operations department prefers to avoid putting any new release into production.

## Values and Goals

Similar to the Agile movement, DevOps has a strong focus on interpersonal aspects. DevOps
is about putting the fun back into IT! However, what does collaboration mean? There are many
prerequisites to cooperation and trust, including the following:

- Respect for one another.
- Commitment to shared goals.
- Collective ownership.
- Shared values.

Aligned with defined quality attributes, visibility and transparency can help to foster collaboration. Incentives must treat the development and operations groups as one team. That is, **they should be rewarded for developing many changes that are stable and shipped**.

cording to Humble and Farley, an “environment is all of the resources that your application needs to work and their configuration” (Continuous Delivery [Addison-Wesley, 2011], page 277), as well as the hardware configuration (including CPUs, memory, and spindles) and the configuration of the operating system and middleware (including messaging systems and web servers). The term infrastructure summarizes all of the environments in your organization together with supporting services, such as firewalls and monitoring systems.

Under automatic releasing, major parts of the release process are per- formed by scripts and tool chains.

In an automatic releasing process, major parts of the process are accomplished automatically. Often, it’s up to the domain expert to decide which release candidate is promoted to release status (e.g., by pressing a specific button)

# Automatic releasing

Releasing is the process of making changes available to the end user. A deployment can result in a release, but that’s not mandatory

SignalFx is a SaaS-based monitoring and analytics platform based in San Mateo, California which allows customers to analyze, visualize, automate, and alert on metrics data from infrastructure, applications, microservices, containers, and functions.[1][2] At the core of the platform is a streaming architecture that splits metric data points into two streams, one for human readable metadata and the other for time-series values. The data is routed through a pub-sub bus to SignalFlow, a python-like analytics language accessible through the main SignalFx GUI and through programmable API's. The platform is able to process millions of data points per second at 1-second resolution with less than 2 seconds of latency, from ingestion to alert.
