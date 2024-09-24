#/usr/bin/env python3

import argparse, json, os, secrets, shutil
from datetime import datetime

parser = argparse.ArgumentParser(description='Oasis setup')
parser.add_argument('--config', type=str, default='oasis-setup-config.json', help='Path to config file')
parser.add_argument('--wireguard-start-port', type=int, default=51000, help='Wireguard start port')
parser.add_argument('--clear', action='store_true', help='Clear all data')
parser.add_argument('--gameserver-log-level', default="info", help='Log level for game server')
parser.add_argument('--max-vm-mem', type=str, default="2G", help='Max memory for VMs')
parser.add_argument('--max-vm-cpus', type=str, default="1", help='Max CPUs for VMs')
parser.add_argument('--privileged', action='store_true', help='Use privilaged mode for VMs')
parser.add_argument('--wireguard-profiles', type=int, default=10, help='Number of wireguard profiles')
parser.add_argument('--dns', type=str, default="1.1.1.1", help='DNS server')
parser.add_argument('--submission-timeout', type=int, default=10, help='Submission timeout rate limit')
parser.add_argument('--flag-expire-ticks', type=int, default=5, help='Flag expire ticks')
parser.add_argument('--initial-service-score', type=int, default=5000, help='Initial service score')
parser.add_argument('--max-flags-per-request', type=int, default=2000, help='Max flags per request')
parser.add_argument('--debug', action='store_true', help='Debug mode')
parser.add_argument('--start-time', type=str, help='Start time (ISO 8601)')
parser.add_argument('--end-time', type=str, help='End time (ISO 8601)')
args = parser.parse_args()

os.chdir(os.path.abspath(os.path.dirname(__file__)))

data = {}
save_config = False
randomize_passwords = False

def try_mkdir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

def dict_to_yaml(data, indent_spaces:int=4, base_indent:int=0, additional_spaces:int=0, add_text_on_dict:str|None=None):
    yaml = ''
    spaces = ' '*((indent_spaces*base_indent)+additional_spaces)
    if isinstance(data, dict):
        for key, value in data.items():
            if not add_text_on_dict is None:
                spaces_len = len(spaces)-len(add_text_on_dict)
                spaces = (' '*max(spaces_len, 0))+add_text_on_dict
                add_text_on_dict = None
            if isinstance(value, dict) or isinstance(value, list):
                yaml += f"{spaces}{key}:\n"
                yaml += dict_to_yaml(value, indent_spaces=indent_spaces, base_indent=base_indent+1, additional_spaces=additional_spaces)
            else:
                yaml += f"{spaces}{key}: {value}\n"
            spaces = ' '*((indent_spaces*base_indent)+additional_spaces)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yaml += dict_to_yaml(item, indent_spaces=indent_spaces, base_indent=base_indent, additional_spaces=additional_spaces+2, add_text_on_dict="- ")
            elif isinstance(item, list):
                yaml += dict_to_yaml(item, indent_spaces=indent_spaces, base_indent=base_indent+1, additional_spaces=additional_spaces)
            else:
                yaml += f"{spaces}- {item}\n"
    else:
        yaml += f"{data}\n"
    return yaml

def generate_teams_array(data):
    teams = []
    for i in range(data['number_of_teams']+ (1 if data['enable_nop_team'] else 0)):
        team = {
            'id': i,
            'name': f'Team {i}',
            'token': secrets.token_hex(32),
            'wireguard_port': data['wireguard_start_port']+i,
            'nop': False,
            'image': "null"
        }
        if i == 0 and data['enable_nop_team']:
            team['nop'] = True
            team['name'] = 'Nop Team'
        teams.append(team)
    return teams

if args.config and os.path.isfile(args.config):
    with open(args.config) as f:
        data = json.load(f)
else:
    while True:
        number_of_teams = int(input('Number of teams: '))
        if number_of_teams < 1:
            print('Number of teams must be greater than 0')
        elif number_of_teams > 250:
            print('Number of teams must be less or equal than 250')
        else:
            break
    data['number_of_teams'] = number_of_teams
    if args.wireguard_start_port <= 0:
        print('Wireguard start port must be greater than 0')
        exit(1)
    elif args.wireguard_start_port+number_of_teams > 65535:
        print(f'Wireguard start port must be less or equal than {args.wireguard_start_port+number_of_teams}')
        exit(1)
    data['wireguard_start_port'] = args.wireguard_start_port
    data['dns'] = args.dns
    data['wireguard_profiles'] = args.wireguard_profiles
    data['docker_privilaged_unsafe'] = args.privilaged
    data['max_vm_cpus'] = args.max_vm_cpus
    data['max_vm_mem'] = args.max_vm_mem
    data['gameserver_token'] = secrets.token_hex(32)
    data['gameserver_log_level'] = args.gameserver_log_level
    data['flag_expire_ticks'] = args.flag_expire_ticks
    data['initial_service_score'] = args.initial_service_score
    data['max_flags_per_request'] = args.max_flags_per_request
    data['start_time'] = datetime.fromisoformat(args.start_time).isoformat() if args.start_time else None
    data['end_time'] = datetime.fromisoformat(args.end_time).isoformat() if args.end_time else None
    data['enable_nop_team'] = input('Enable NOP team? (Y/n): ').lower() != 'n'
    data['server_addr'] = input('Server address: ')
    
    data['submission_timeout'] = args.submission_timeout
    while True:
        try:
            data['tick_time'] = abs(int(input('Tick time (s): ')))
            break
        except Exception:
            print('Invalid tick time')
            pass
    data['teams'] = generate_teams_array(data)
    with open(args.config, 'w') as f:
        json.dump(data, f, indent=4)

config = {
    "services": {
        "router": {
            "hostname": f"router",
            "dns": [data['dns']],
            "build": "./router",
            "cap_add": [
                "NET_ADMIN",
                "SYS_MODULE"
            ],
            "sysctls": [
                "net.ipv4.ip_forward=1",
                "net.ipv4.tcp_timestamps=0"
            ],
            "environment": {
                "NTEAM": len(data['teams'])
            },
            "volumes": [
                "unixsk:/unixsk/"
            ],
            "restart": "unless-stopped",
            "networks": {
                **{f"vm-team{team['id']}": {
                    "priority": 10,
                    "ipv4_address": f"10.60.{team['id']}.250"
                } for team in data['teams']},
                "gameserver": {
                    "priority": 10,
                    "ipv4_address": "10.10.0.250"
                },
                "externalnet": {
                    "priority": 1,
                },
                **{
                    f"players{team['id']}":{
                        "priority": 10,
                        "ipv4_address": f"10.80.{team['id']}.250"
                    } for team in data['teams'] if not team['nop']
                }

            }
        },
         "database": {
            "hostname": f"oasis-database",
            "dns": [data['dns']],
            "image": "postgres",
            "restart": "unless-stopped",
            "environment": {
                "POSTGRES_USER": "oasis",
                "POSTGRES_PASSWORD": "oasis",
                "POSTGRES_DB": "oasis"
            },
            "volumes": [
                "./volumes/database/:/var/lib/postgresql/data"
            ],
            **({
                "ports": [
                    "5432:5432"
                ]
            } if args.debug else {}),
            "networks": {
                "internalnet": "",
            }
        },
        "gameserver": {
            "hostname": f"gameserver",
            "dns": [data['dns']],
            "build": "./game_server",
            "restart": "unless-stopped",
            "cap_add": [
                "NET_ADMIN"
            ],
            "depends_on": [
                "router",
                "database"
            ],
            **({
                "ports": [
                    "8888:80",
                    "8080:8080",
                    "8081:8081"
                ]
            } if args.debug else {}),
            "networks": {
                "internalnet": {
                    "priority": 1
                },
                "gameserver": {
                    "priority": 10,
                    "ipv4_address": "10.10.0.1"
                }
            },
            "volumes": [
                "./game_server/checkers/:/app/checkers/",
                "unixsk:/unixsk/"
            ]
        },
        **{
            f"team{team['id']}": {
                "hostname": f"team{team['id']}",
                "dns": [data['dns']],
                "build": {
                    "context": "./vm",
                    "args": {
                        "TOKEN": team['token'],
                        "TEAM_NAME": team['name'],
                    }
                },
                **({"privileged": "true"} if data['docker_privilaged_unsafe'] else { "runtime": "sysbox-runc" }),
                "restart": "unless-stopped",
                "volumes": [
                    f"./volumes/team{team['id']}-root/:/root/"
                ],
                "networks": {
                    f"vm-team{team['id']}": {
                        "ipv4_address": f"10.60.{team['id']}.1"
                    }
                },
                "deploy":{
                    "resources":{
                        "limits":{
                            "cpus": f'"{data["max_vm_cpus"]}"',
                            "memory": data['max_vm_mem']
                        }
                    }
                }
            } for team in data['teams']
        },
        **{
            f"wireguard{team['id']}": {
                "hostname": f"wireguard{team['id']}",
                "dns": [data['dns']],
                "build": "./wireguard",
                "restart": "unless-stopped",
                "cap_add": [
                    "NET_ADMIN"
                ],
                "sysctls": [
                    "net.ipv4.conf.all.src_valid_mark=1",
                    "net.ipv4.ip_forward=1"
                ],
                "volumes": [
                    f"./wireguard/conf{team['id']}/:/config/"
                ],
                "networks": {
                    f"players{team['id']}": {
                        "ipv4_address": f"10.80.{team['id']}.128"
                    }
                },
                "ports": [
                    f"{data['wireguard_start_port']+team['id']}:51820/udp"
                ],
                "environment": {
                    "PUID": 1000,
                    "PGID": 1000,
                    "TZ": "Etc/UTC",
                    "PEERS": data['wireguard_profiles'],
                    "PEERDNS": data['dns'],
                    "ALLOWEDIPS": "10.10.0.0/16, 10.60.0.0/16, 10.80.0.0/16",
                    "SERVERURL": data['server_addr'],
                    "SERVERPORT": data['wireguard_start_port']+team['id'],
                    "INTERNAL_SUBNET": f"10.80.{team['id']}.0/24",
                }
            } for team in data['teams'] if not team['nop']
        }
    },
    "volumes": {
        "unixsk": "",
    },
    "networks": {
        "externalnet": {
            "driver": "bridge",
            "driver_opts": {
                "com.docker.network.bridge.enable_icc": '"false"'
            },
        },
        "internalnet": "",
        "gameserver": {
            "internal": "true",
            "driver": "macvlan",
            "ipam": {
                "driver": "default",
                "config": [
                    {
                        "subnet": "10.10.0.0/24",
                        "gateway": "10.10.0.254",
                    }
                ]
            }
        },
        **{
            f"vm-team{team['id']}": {
                "internal": "true",
                "driver": "macvlan",
                "ipam": {
                    "driver": "default",
                    "config": [
                        {
                            "subnet": f"10.60.{team['id']}.0/24",
                            "gateway": f"10.60.{team['id']}.254",
                        }
                    ]
                }
            } for team in data['teams']
        },
        **{
            f"players{team['id']}": {
                "driver": "bridge",
                "ipam": {
                    "driver": "default",
                    "config": [
                        {
                            "subnet": f"10.80.{team['id']}.0/24",
                            "gateway": f"10.80.{team['id']}.254",
                        }
                    ]
                }
            } for team in data['teams'] if not team['nop']
        }
    }
}

if args.clear:
    shutil.rmtree("./volumes", ignore_errors=True)
    for file in os.listdir("./wireguard"):
        if file.startswith("conf"):
            shutil.rmtree(f"./wireguard/{file}", ignore_errors=True)

try_mkdir("./volumes")

with open('compose.yml', 'w') as f:
    f.write(dict_to_yaml(config))
    
print('Config saved to compose.yml')

nop_team = data['teams'][0]['id'] if data['enable_nop_team'] else None

gameserver_config = {
    "log_level": data['gameserver_log_level'] if not args.debug else "debug",
    "round_len": data['tick_time']*1000,
    "token": data['gameserver_token'],
    "nop": f"10.60.{nop_team}.1" if not nop_team is None else "null",
    "submitter_limit": data['submission_timeout']*1000,
    "teams": {
        **{
            f"10.60.{team['id']}.1": {
                "token": team['token'],
                "name": team['name'],
                "image": team['image']
            } for team in data['teams']
        },
    },
    "flag_expire_ticks": data['flag_expire_ticks'],
    "initial_service_score": data['initial_service_score'],
    "max_flags_per_request": data['max_flags_per_request'],
    "start_time": data['start_time'] if data['start_time'] else "null",
    "end_time": data['end_time'] if data['end_time'] else "null",
    "debug": "true" if args.debug else "false",
}

with open('game_server/src/config.yml', 'w') as f:
    f.write(dict_to_yaml(gameserver_config))

print('Game server config saved to game_server/src/config.yml')

if not data['docker_privilaged_unsafe']:
    print('Please install sysbox! https://github.com/nestybox/sysbox , or use --privilaged flag to use default docker runtime (unsecure)')

print('\nUse: "docker compose exec router ctfroute unlock" to start the ctf!')

