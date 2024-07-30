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

Install the necessary dependencies:

```bash
pip install -r requirements.txt
```

Configure the services and infrastructure as needed, using the provided compose.yml file:

```bash
docker-compose up -d
```

## Usage
Running Services
To run the services included in the Oasis project:

Navigate to the appropriate service directory, for example:

```bash
cd game_server/checkers
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
