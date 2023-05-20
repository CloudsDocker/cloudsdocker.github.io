---
title: UUID deep dive
header:
    image: /assets/images/uuid-deep-div.jpg
date: 2023-05-08
tags:
- AI
- stripe
- automation

permalink: /blogs/tech/en/uuid-deep-div
layout: single
category: tech
---
> A young idler, an old beggar. - William Shakespeare

# What's UUID
Here are some examples of V4 UUIDs:

```
87b9c35f-ffdc-4d72-85f6-49f6d1d6b499
9e6bdc55-cd3d-4dd7-bad4-e6ec8368f227
c4b7f530-5a2a-4b05-bf5c-7c4ebca20f4c
4df0c7b5-5fa5-4d48-b0e5-7b12715dc261
81034e08-2a7e-4f9b-bc21-6cd3c6b977c6
```

## Quick notes:
- UUID stands for Universally Unique Identifier
- UUIDs are 128-bit numbers used to uniquely identify objects or entities in computer systems
- Format is always 8-4-4-4-12
- There are 5 sections in a UUID, separated by hyphens- 
- There are 36 characters in a UUID, including the hyphens-
- The letters in the UUIDs are always lowercase
- UUID version 4 is generated randomly using a combination of the current time, a random number, and the MAC address of the computer generating the UUID
- The probability of two version 4 UUIDs colliding is extremely low, so low that it is often considered negligible for most practical purposes
- UUID version 4 is widely used in software development for a variety of purposes such as generating unique session identifiers, tracking objects, and creating random passwords
- UUID version 4 is also used in distributed systems where unique identifiers are needed
- UUID version 4 is also used in cryptography to generate random numbers for encryption keys
- UUID version 4 is also used in the healthcare industry to generate unique patient identifiers
- UUID version 4 is also used in the financial industry to generate unique transaction identifiers
- UUID version 4 is also used in the gaming industry to generate unique player identifiers
- UUID version 4 is also used in the automotive industry to generate unique vehicle identifiers
- UUID version 4 is also used in the aerospace industry to generate unique aircraft identifiers
- UUID version 4 is also used in the military to generate unique soldier identifiers
- UUID version 4 is also used in the education industry to generate unique student identifiers
- UUID version 4 is also used in the retail industry to generate unique customer identifiers

Note that the letters in the UUIDs are always lowercase, and the format is always 8-4-4-4-12, meaning that the UUID is broken up into five groups of characters, with the first group containing eight characters, the next three groups containing four characters each, and the final group containing twelve characters.

# Understanding UUID Version 4

UUIDs (Universally Unique Identifiers) are 128-bit numbers used to uniquely identify objects or entities in computer systems. There are several versions of UUID, each with a different method of generating the unique identifier. In this blog, we'll focus on UUID version 4.

## What is UUID Version 4?

UUID version 4 is generated randomly using a combination of the current time, a random number, and the MAC address of the computer generating the UUID. It's also known as a "random UUID" because it doesn't contain any information about the system or the time it was generated.

## How is UUID Version 4 Generated?

UUID version 4 is generated using a random number generator, which generates 122 random bits. The two most significant bits of the first octet are set to binary '10', and the two most significant bits of the second octet are set to binary '01'. This creates a UUID with a total of 32 hexadecimal digits, with hyphens separating the digits into five groups.

## Probability of Collision

The probability of two version 4 UUIDs colliding is extremely low, so low that it is often considered negligible for most practical purposes. This makes UUID version 4 suitable for use in distributed systems where unique identifiers are needed.

## Uses of UUID Version 4

UUID version 4 is widely used in software development for a variety of purposes such as generating unique session IDs, creating unique file names, and identifying resources in distributed systems. It can be generated using a variety of programming languages, including Python, Java, C++, and Ruby.

## Conclusion

UUID version 4 is a simple and reliable way to generate unique identifiers in software systems. It is widely used in many different programming languages and environments for a variety of purposes, and the probability of collision is so low that it is often considered negligible.

# Understanding the Different Versions of UUID

UUIDs (Universally Unique Identifiers) are 128-bit numbers used to uniquely identify objects or entities in computer systems. There are several versions of UUID, each with a different method of generating the unique identifier. In this blog, we'll discuss the different versions of UUID.

## Version 1

UUID version 1 is generated using the MAC address of the computer and a timestamp. This version is not recommended for security reasons, as it can be traced back to the computer that generated it.

## Version 2

UUID version 2 is similar to version 1, but also includes a "domain" identifier, which can be used to identify the security domain that the UUID was generated in.

## Version 3

UUID version 3 is generated using a hashing algorithm, and is based on a namespace and a name that is unique within that namespace.

## Version 4

UUID version 4 is generated randomly using a combination of the current time, a random number, and the MAC address of the computer generating the UUID. It is also known as a "random UUID" because it does not contain any information about the system or the time it was generated.

## Version 5

UUID version 5 is similar to version 3, but uses a different hashing algorithm.

## Conclusion

There are several versions of UUID, each with its own method of generating a unique identifier. Versions 1 and 2 are considered legacy versions and are not recommended for use due to privacy and security concerns. Versions 3, 4, and 5 are all widely used today, with version 4 being the most commonly used. UUIDs are widely used in software development for a variety of purposes, including generating unique session IDs, creating unique file names, and identifying resources in distributed systems.


--HTH--
