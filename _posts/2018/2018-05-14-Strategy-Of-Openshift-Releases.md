---
title: Strategy-Of-Openshift-Releases
tags:
- clud
- Openshift
layout: posts
---

# Release & Testing Strategy
There are various methods for safely releasing changes to Production. Each team must select what is appropriate for their own use case with consideration to risk, rollback approaches and testing approaches.

# The following are options:

## Canary Release
This is the lowest risk strategy since it allows for testing on a subset of users, and it allows for fast rollback:

* Build a new Environment
* Use a routing tool (eg. Apigee) to test with a specific set of users
* Bleed traffic across
* Remove old environment

## Blue Green
 This is the classic zero-downtime deployment model that involves flipping traffic between two environments:
* Ensure your router has two entry points, one for Production Testing and one for Production traffic
* Have two environments: `blue` and `green`
* If Production traffic is pointing to `blue` then deploy your changes on `green`
* Point your Production Testing traffic to `green`
* When verified, point Production traffic to `green`
* On the next release, deploy changes to `blue`

