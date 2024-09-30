# Oasis

- Open
- Attack & Defense
- Simple
- Infrastructure
- System

## Introduction
Oasis is an open-source project designed to provide a simple and robust infrastructure for attack and defense simulations. It facilitates cybersecurity training and testing through various components and services.


## Table of Contents
[Introduction](#introduction)
[Installation](#installation)
[Usage](#usage)
[Features](#features)
[Configuration](#configuration)
[Documentation](#documentation)


## Installation
To install and set up the Oasis project, follow these steps:

Clone the repository:

```bash
git clone https://github.com/yourusername/Oasis.git
cd Oasis
```

Install sysbox (you need to use a fixed version of sysbox in this repository until the official release will be released and the issue will be fixed):

📦 [Sysbox .deb files here (for x86 and arm64)](sysbox-fix)

If you can't install sysbox you can still run Oasis but using privileged docker mode, that is not recommended for security reasons.

Create compose.yml file:

```bash
python3 start.py start
```

if you want to use privileged mode, you can use the following command:

```bash
#UNSAFE, DON'T SHARE VMs WITH UNTRUSTED USERS
python3 setup.py start --privileged
```

Build the Docker containers:

```bash
docker compose up -d --build
```

To connect to the VMs, you need to use one of the wireguard configurations in the wireguard folder.

Instead you can run `python3 start.py compose exec team<team_id> bash` to connect to the VMs.

To manage the game network run:

```bash 
python3 start.py compose exec router ctfroute unlock|lock
```

This will be automatically handled by the game server. For special cases, you can use this command.

To stop the services run:

```bash
python3 start.py stop --clean # Only if you want remove all the volumes and configs
```

## Usage
Running Services
To run the services included in the Oasis project:

Navigate to the appropriate service directory, for example:

```bash
cd gameserver/checkers
```

Execute the service using the provided scripts:

```bash
python checker.py
```

Check SLA
```bash
ACTION=CHECK_SLA TEAM_ID=0 ROUND=0 ./checker.py
```
Put Flag
```bash
ACTION=PUT_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py
```

Get Flag
```bash
ACTION=GET_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py
```

## Features
- Attack and Defense Simulations: Simulate various cybersecurity attack and defense scenarios.
- Multiple Services: Includes services like Notes and Polls with checkers and exploits for each.
- Infrastructure Setup: Uses Docker Compose for easy setup and management of the infrastructure.
- Extensible: Easily add new services, checkers, and exploits.


## Configuration
#### Docker Compose
The compose.yml file includes configurations for setting up the necessary Docker containers and networks. Adjust the configurations as needed for your environment.


## Documentation
For detailed documentation on each component and service, refer to the respective README.md files in their directories:

- Checkers
- Exploits
- Service 1 - Notes
- Service 2 - Polls
