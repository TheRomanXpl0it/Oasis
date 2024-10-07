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
[Configuration](#configuration)
[Usage](#usage)
[Features](#features)


## Installation
To install and set up the Oasis project, follow these steps:

Clone the repository:

```bash
git clone https://github.com/yourusername/Oasis.git
cd Oasis
```

For running Oasis, you need podman (docker cannot be used due to avoid using privileged containers) installed and docker-compose or podman-compose.
After that you can run the following command to start the Oasis infrastructure:

```bash
python3 start.py start
```

To connect to the VMs, you need to use one of the wireguard configurations in the wireguard folder.

Instead you can run `python3 start.py compose exec team<team_id> bash` to connect to the VMs.

To manage the game network run:

```bash 
python3 start.py compose exec router ctfroute unlock|lock
```

This will be automatically handled by the game server based on the configuration given (start_time, end_time, customizable from the oasis json). For special cases, you can use this command.

## Configuration

If you want generate the Oasis json config, edit it and after start Oasis run:

```bash
python3 start.py start -C
```

This will generate the config only, you can start oasis later

To stop the services run:

```bash
python3 start.py stop
python3 start.py --clean # Only if you want remove all the volumes and configs
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
SERVICE=ServiceName ACTION=CHECK_SLA TEAM_ID=0 ROUND=0 ./checker.py
```
Put Flag
```bash
SERVICE=ServiceName ACTION=PUT_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py
```

Get Flag
```bash
SERVICE=ServiceName ACTION=GET_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py
```

## Features
- Attack and Defense Simulations: Simulate various cybersecurity attack and defense scenarios.
- Multiple Services: Includes services like Notes and Polls with checkers and exploits for each.
- Infrastructure Setup: Uses Docker Compose for easy setup and management of the infrastructure.
- Extensible: Easily add new services, checkers, and exploits.
