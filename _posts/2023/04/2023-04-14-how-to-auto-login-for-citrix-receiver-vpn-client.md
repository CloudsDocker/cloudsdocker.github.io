---
title: How To Install Sonarqube Via Docker
header:
    image: /assets/images/how-to-install-sonarqube-via-docker.jpg
date: 2023-04-14
tags:
- ssh
- devops
- automation

permalink: /blogs/tech/en/how-to-install-sonarqube-via-docker
layout: single
category: tech
---

> "Hang Out with People Who are Better than You." — Warren Buffett

# SonarQube Community Edition in Docker guidance
SonarQube is an open-source tool for continuous code quality inspection. It provides a comprehensive platform for static code analysis, code coverage, and other quality metrics. In this guide, we will walk you through the process of installing SonarQube Community Version.

## Prerequisites:

A machine running Windows, Linux or MacOS
Java JDK 11 or above installed on the machine
Sufficient privileges to install software on the machine

here's a step-by-step guide to installing and setting up SonarQube Community Version in Docker on MacOS:

Install Docker Desktop for Mac: You can download the Docker Desktop installer from the Docker website and follow the installation instructions.

Pull the SonarQube Community Edition image: Open a terminal window and enter the following command to download the SonarQube image from the Docker Hub:

```shell
docker pull sonarqube:community
```

Create a Docker network: Run the following command to create a network for the SonarQube container to communicate with other Docker containers:


```shell
docker network create sonarnet
```
Start the SonarQube container: Run the following command to start the SonarQube container with the required environment variables:


```shell
docker run -d --name sonarqube \
-p 9000:9000 \
--network sonarnet \
-e sonar.jdbc.url=jdbc:postgresql://db:5432/sonar \
-e sonar.jdbc.username=sonar \
-e sonar.jdbc.password=sonar \
sonarqube:community
```
This command starts the SonarQube container in detached mode, binds the container port 9000 to the host port 9000, and sets the database configuration parameters.

Start a PostgreSQL container: SonarQube requires a PostgreSQL database to store its data. Run the following command to start a PostgreSQL container:
here's a step-by-step guide to installing and setting up SonarQube Community Version in Docker on MacOS:

Install Docker Desktop for Mac: You can download the Docker Desktop installer from the Docker website and follow the installation instructions.

Pull the SonarQube Community Edition image: Open a terminal window and enter the following command to download the SonarQube image from the Docker Hub:

```shell
docker pull sonarqube:community
```
Create a Docker network: Run the following command to create a network for the SonarQube container to communicate with other Docker containers:


```shell
docker network create sonarnet
```
Start the SonarQube container: Run the following command to start the SonarQube container with the required environment variables:


```shell
docker run -d --name sonarqube \
-p 9000:9000 \
--network sonarnet \
-e sonar.jdbc.url=jdbc:postgresql://db:5432/sonar \
-e sonar.jdbc.username=sonar \
-e sonar.jdbc.password=sonar \
sonarqube:community
```
This command starts the SonarQube container in detached mode, binds the container port 9000 to the host port 9000, and sets the database configuration parameters.

Start a PostgreSQL container: SonarQube requires a PostgreSQL database to store its data. Run the following command to start a PostgreSQL container:

```shell
docker run -d --name db \
--network sonarnet \
-e POSTGRES_USER=sonar \
-e POSTGRES_PASSWORD=sonar \
-e POSTGRES_DB=sonar \
postgres:13
```
This command starts a PostgreSQL container with the required environment variables and adds it to the sonarnet network.

Verify the installation: Wait a few minutes for the containers to start up, and then open a web browser and navigate to http://localhost:9000. You should see the SonarQube login page.
That's it! You have now installed and set up SonarQube Community Version in Docker on MacOS. You can use the SonarQube web interface to analyze your code and detect issues.

```shell
docker run -d --name db \
--network sonarnet \
-e POSTGRES_USER=sonar \
-e POSTGRES_PASSWORD=sonar \
-e POSTGRES_DB=sonar \
postgres:13
```
This command starts a PostgreSQL container with the required environment variables and adds it to the sonarnet network.

Verify the installation: Wait a few minutes for the containers to start up, and then open a web browser and navigate to http://localhost:9000. You should see the SonarQube login page.
That's it! You have now installed and set up SonarQube Community Version in Docker on MacOS. You can use the SonarQube web interface to analyze your code and detect issues.





--HTH--
