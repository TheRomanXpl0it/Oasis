# Oasis

- Open
- Attack & Defense
- Simple
- Infrastructure
- System

![screencapture_scoreboard_ad_pwnzer0tt1_it_scoreboard_2024_10_26](https://github.com/user-attachments/assets/bdab4b38-d919-44f9-af72-c0422c14129d)

## Introduction
Oasis is an open-source project designed to provide a simple infrastructure for attack and defense simulations. It facilitates cybersecurity training and testing through various components and services.


## Installation
To install and set up the Oasis project, follow these steps:

Clone the repository:

```bash
git clone https://github.com/yourusername/Oasis.git
cd Oasis
```

For running Oasis, you need docker and have correctly installed and configured [sysbox](https://github.com/nestybox/sysbox).

You can install sysbox with the official .deb files in the repository, or using AUR for Arch Linux, or even [using dnf copr](https://copr.fedorainfracloud.org/coprs/karellen/karellen-sysbox/) for Fedora. (The only official supported way is the .deb files, but the other methods are also working)

Remember that after installing you need to enable sysbox services, and also config docker adding the following lines to `/etc/docker/daemon.json`:
```json
{
    "runtimes": {
        "sysbox-runc": {
            "path": "/usr/bin/sysbox-runc"
        }
    }
}
```

After that, restart the docker service.

Now you can run Oasis using the following command:

```bash
sudo python3 start.py start
```

NOTE: You can avoid to use sysbox by using --privileged mode, but this is not recommended if the VMs are given to untrusted users. The --privileged mode will give
access to some hosts functionality to the VMs, and escape from container is possible. If you want to use it, you can run:

```bash
sudo python3 start.py start --privileged
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
python3 start.py --clean # Only if you want remove all the volumes except configs
```

Before run the competition, you can customize additional settings in the `oasis-setup-config.json` file:

- `wireguard_start_port`: The starting port for WireGuard connections.
- `dns`: The DNS server to be used internally in the network.
- `wireguard_profiles`: The number of WireGuard profiles to be created for each team.
- `max_vm_cpus`: The maximum number of CPUs allocated to each VM.
- `max_vm_mem`: The maximum amount of memory allocated to each VM.
- `gameserver_token`: The token used for the game server. (It's also the password login for the credential server)
- `gameserver_log_level`: The log level for the game server. (info, debug, error)
- `flag_expire_ticks`: The number of ticks after which a flag expires.
- `initial_service_score`: The initial score for each service.
- `max_flags_per_request`: The maximum number of flags that can be submitted in a single request.
- `start_time`: The start time of the competition (can be null of an string with the ISO format).
- `end_time`: The end time of the competition (can be null of an string with the ISO format).
- `submission_timeout`: The timeout for flag submissions in seconds.
- `server_addr`: The public address of the server (used for the wireguard config).
- `network_limit_bandwidth`: The bandwidth limit for each server (e.g., "20mbit").
- `max_disk_size`: The maximum disk size for each VM (e.g., "30G"). (YOU NEED TO HAVE XFS FILESYSTEM and -D flag in the start.py command)
- `debug`: Enable debug mode for the game server.
- `tick_time`: The time in seconds for each tick.
- `teams`: A list of teams with their respective configurations:
  - `id`: The ID of the team.
  - `name`: The name of the team.
  - `token`: The token for the team (used for flag submission and server password).
  - `wireguard_port`: The port for WireGuard connections for the team.
  - `nop`: True if the team is marked as NOP team (will not have a wireguard access server).
  - `image`: (Optional) The image used by the team for the scoreboard (more images can be added in the frontend).

## Credential Service

You can also give wireguard profile and password and ip to each team member using the credential_service that is a separate
service that could be runned using docker compose, that will read and write pins that can be used to access the competition.
The webplatform will require a PIN to login and access to download the wireguard profile and on the team token.
Admins can access and read PIN on /admin page, loggin in with the gameserver token.

## Features
- Attack and Defense Simulations: Simulate various cybersecurity attack and defense scenarios.
- Multiple Services: Includes services like Notes and Polls with checkers and exploits for each.
- Infrastructure Setup: Uses Docker Compose for easy setup and management of the infrastructure.
- Extensible: Easily add new services, checkers, and exploits.
