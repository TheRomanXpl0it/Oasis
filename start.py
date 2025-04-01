#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
import os
import subprocess
import json
import secrets
import shutil
from datetime import datetime

pref = "\033["
reset = f"{pref}0m"

class g:
    keep_file = False
    composefile = "oasis-compose-tmp-file.yml"
    container_name = "oasis_gameserver"
    compose_project_name = "oasis"
    name = "Oasis"
    config_file = "oasis-setup-config.json"
    gammeserver_config_file = "game_server/config.yml"
    prebuild_image = "oasis-prebuilder"
    prebuilded_container = "oasis-prebuilded"
    prebuilt_image = "oasis-vm-base"

use_build_on_compose = True

os.chdir(os.path.dirname(os.path.realpath(__file__)))

#Terminal colors

class colors:
    black = "30m"
    red = "31m"
    green = "32m"
    yellow = "33m"
    blue = "34m"
    magenta = "35m"
    cyan = "36m"
    white = "37m"

def dict_to_yaml(data, indent_spaces:int=4, base_indent:int=0, additional_spaces:int=0, add_text_on_dict:str|None=None):
    yaml = ''
    spaces = ' '*((indent_spaces*base_indent)+additional_spaces)
    if isinstance(data, dict):
        for key, value in data.items():
            if add_text_on_dict is not None:
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

def puts(text, *args, color=colors.white, is_bold=False, **kwargs):
    print(f'{pref}{1 if is_bold else 0};{color}' + text + reset, *args, **kwargs)

def sep(): puts("-----------------------------------", is_bold=True)

def cmd_check(program, get_output=False, print_output=False, no_stderr=False):
    if get_output:
        return subprocess.getoutput(program)
    if print_output:
        return subprocess.call(program, shell=True) == 0
    return subprocess.call(program, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL if no_stderr else subprocess.STDOUT, shell=True) == 0

def composecmd(cmd, composefile=None):
    if composefile:
        cmd = f"-f {composefile} {cmd}"
    if not cmd_check("podman --version"):
        return puts("Podman not found! please install podman!", color=colors.red)
    elif not cmd_check("podman ps"):
        return puts("Cannot use podman, the user hasn't the permission or podman isn't running", color=colors.red)
    elif cmd_check("podman compose --version"):
        return os.system(f"podman compose -p {g.compose_project_name} {cmd}")
    elif cmd_check("podman-compose --version"):
        return os.system(f"podman-compose -p {g.compose_project_name} {cmd}")
    else:
        return puts("Podman compose not found! please install podman compose!", color=colors.red)

def check_already_running():
    return g.container_name in cmd_check(f'podman ps --filter "name=^{g.container_name}$"', get_output=True)

def prebuilder_exists():
    return g.prebuild_image in cmd_check(f'podman image ls --filter "reference={g.prebuild_image}"', get_output=True)

def prebuilt_exists():
    return g.prebuilt_image in cmd_check(f'podman image ls --filter "reference={g.prebuilt_image}"', get_output=True)

def remove_prebuilder():
    return cmd_check(f'podman image rm {g.prebuild_image}')

def remove_prebuilt():
    return cmd_check(f'podman image rm {g.prebuilt_image}')

def remove_prebuilded():
    return cmd_check(f'podman container rm {g.prebuilded_container}')

def remove_database_volume():
    return cmd_check('podman volume rm -f oasis_oasis-postgres-db')

def build_prebuilder():
    return cmd_check(f'podman build -t {g.prebuild_image} -f ./vm/Dockerfile.prebuilder ./vm/', print_output=True)

def build_prebuilt():
    return cmd_check(f'podman run -it --device /dev/fuse --cap-add audit_write,net_admin --security-opt label=disable --name {g.prebuilded_container} {g.prebuild_image}', print_output=True)

def kill_builder():
    return cmd_check(f'podman kill {g.prebuilded_container}', no_stderr=True)

def commit_prebuilt():
    return cmd_check(f'podman commit {g.prebuilded_container} {g.prebuilt_image}:latest', print_output=True)

def gen_args(args_to_parse: list[str]|None = None):                     
    
    #Main parser
    parser = argparse.ArgumentParser(description=f"{g.name} Manager")

    subcommands = parser.add_subparsers(dest="command", help="Command to execute", required=True)
    
    #Compose Command
    parser_compose = subcommands.add_parser('compose', help='Run podman compose command')
    parser_compose.add_argument('compose_args', nargs=argparse.REMAINDER, help='Arguments to pass to podman compose', default=[])
    
    #Start Command
    parser_start = subcommands.add_parser('start', help=f'Start {g.name}')
    parser_start.add_argument('--logs', required=False, action="store_true", help=f'Show {g.name} logs', default=False)
    #Gameserve options
    parser_start.add_argument('--wireguard-start-port', type=int, default=51000, help='Wireguard start port')
    parser_start.add_argument('--gameserver-log-level', default="info", help='Log level for game server')
    parser_start.add_argument('--max-vm-mem', type=str, default="2G", help='Max memory for VMs')
    parser_start.add_argument('--max-vm-cpus', type=str, default="1", help='Max CPUs for VMs')
    parser_start.add_argument('--wireguard-profiles', type=int, default=30, help='Number of wireguard profiles')
    parser_start.add_argument('--dns', type=str, default="1.1.1.1", help='DNS server')
    parser_start.add_argument('--submission-timeout', type=int, default=10, help='Submission timeout rate limit')
    parser_start.add_argument('--flag-expire-ticks', type=int, default=5, help='Flag expire ticks')
    parser_start.add_argument('--initial-service-score', type=int, default=5000, help='Initial service score')
    parser_start.add_argument('--max-flags-per-request', type=int, default=2000, help='Max flags per request')
    parser_start.add_argument('--start-time', type=str, help='Start time (ISO 8601)')
    parser_start.add_argument('--end-time', type=str, help='End time (ISO 8601)')
    parser_start.add_argument('--max-disk-size', type=str, default="30G", help='Max disk size for VMs')
    parser_start.add_argument('--network-limit-bandwidth', type=str, default="20mbit", help='Network limit bandwidth')
    #init options
    parser_start.add_argument('--privileged', '-P', action='store_true', help='Use privileged mode for VMs')
    parser_start.add_argument('--expose-gameserver', '-E', action='store_true', help='Expose gameserver port')
    parser_start.add_argument('--gameserver-port', default="127.0.0.1:8888", help='Gameserver port')
    parser_start.add_argument('--config-only', '-C', action='store_true', help='Only generate config file')
    parser_start.add_argument('--disk-limit', '-D', action='store_true', help='Limit disk size for VMs (NEED TO ENABLE QUOTAS)')

    #Stop Command
    parser_stop = subcommands.add_parser('stop', help=f'Stop {g.name}')
    
    #Restart Command
    parser_restart = subcommands.add_parser('restart', help=f'Restart {g.name}')
    parser_restart.add_argument('--logs', required=False, action="store_true", help=f'Show {g.name} logs', default=False)
    parser_restart.add_argument('--privileged', '-P', action='store_true', help='Use privileged mode for VMs')
    parser_restart.add_argument('--disk-limit', '-D', action='store_true', help='Limit disk size for VMs')
    parser_restart.add_argument('--expose-gameserver', '-E', action='store_true', help='Expose gameserver port')
    parser_restart.add_argument('--gameserver-port', default="127.0.0.1:8888", help='Gameserver port')

    #Clear Command
    parser_clear = subcommands.add_parser('clear', help='Clear data')
    parser_clear.add_argument('--all', '-A', action='store_true', help='Clear everything')
    parser_clear.add_argument('--config', '-C', action='store_true', help='Clear config file')
    parser_clear.add_argument('--prebuilded-container', '-P', action='store_true', help='Clear prebuilded container')
    parser_clear.add_argument('--prebuilder-image', '-B', action='store_true', help='Clear prebuilder image')
    parser_clear.add_argument('--prebuilt-image', '-I', action='store_true', help='Clear prebuilt image')
    parser_clear.add_argument('--wireguard', '-W', action='store_true', help='Clear wireguard data')
    parser_clear.add_argument('--checkers-data', '-D', action='store_true', help='Clear checkers data')
    parser_clear.add_argument('--gameserver-config', '-G', action='store_true', help='Clear gameserver config')
    parser_clear.add_argument('--gameserver-data', '-D', action='store_true', help='Clear gameserver data')
    
    subcommands.add_parser('enable-quotas', help='Enable quotas for VMs (Need XFS and this file has to be running directly in the host) (Need to be run only once)')
    
    args = parser.parse_args(args=args_to_parse)
    
    if "privileged" not in args:
        args.privileged = False
        
    if "expose_gameserver" not in args:
        args.expose_gameserver = False
        
    if "gameserver_port" not in args:
        args.gameserver_port = "127.0.0.1:8888"
    
    if "disk_limit" not in args:
        args.disk_limit = False
    
    if not check_for_quotas() and args.disk_limit:
        if not ask_for_quota_command():
            exit(1)

    return args

def ask_for_quota_command():
    print("This command will set some settings for podman to enable quotas")
    print("- Run this only once")
    print("- Run me directly in the host that runs the containers")
    print("- Run me with root privilages")
    puts("If one of these conditions are not met, please cancel this command", color=colors.red)
    if input('You are running the command correctly? (y/N): ').lower() == 'y':
        enable_quotas()
        puts("Quotas enabled!", color=colors.green)
        return True
    else:
        puts("Operation cancelled", color=colors.red)
        return False


quota_setting_xfs = [
    ("100000:/var/lib/containers/storage/overlay", "/etc/projects"),
    ("200000:/var/lib/containers/storage/volumes", "/etc/projects"),
    ("storage:100000", "/etc/projid"),
    ("volumes:200000", "/etc/projid"),
]

def check_for_quotas():
    for data_to_write, filename in quota_setting_xfs:
        try:
            with open(filename, 'r') as f:
                data = f.read()
            if data_to_write not in data:
                return False
        except FileNotFoundError:
            return False
    return True

def enable_quotas():
    for data_to_write, filename in quota_setting_xfs:
        try:
            with open(filename, 'r') as f:
                data = f.read()
        except FileNotFoundError:
            data = ""
        if data_to_write not in data:
            with open(filename, 'a') as f:
                f.write(data_to_write+'\n')

    if not cmd_check("xfs_quota -x -c 'project -s storage volumes' /", print_output=True):
        puts("Failed to setup xfs quotas", color=colors.red)
        exit(1)



args = gen_args()

def write_compose(data):
    with open(g.composefile,"wt") as compose:
        compose.write(dict_to_yaml({
            "services": {
                "router": {
                    "hostname": "router",
                    "dns": [data['dns']],
                    "build": "./router",
                    "cap_add": [
                        "NET_ADMIN",
                        "SYS_MODULE",
                        "SYS_ADMIN",
                    ],
                    "sysctls": [
                        "net.ipv4.ip_forward=1",
                        "net.ipv4.tcp_timestamps=0",
                        "net.ipv4.conf.all.rp_filter=1",
                        "net.ipv6.conf.all.forwarding=0",
                        "net.ipv6.conf.eth0.autoconf=0"
                    ],
                    "environment": {
                        "NTEAM": len(data['teams']),
                        "RATE_NET": data['network_limit_bandwidth'],
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
                    "hostname": "oasis-database",
                    "dns": [data['dns']],
                    "image": "postgres:17",
                    "restart": "unless-stopped",
                    "environment": {
                        "POSTGRES_USER": "oasis",
                        "POSTGRES_PASSWORD": "oasis",
                        "POSTGRES_DB": "oasis"
                    },
                    "volumes": [
                        "oasis-postgres-db:/var/lib/postgresql/data"
                    ],
                    "networks": {
                        "internalnet": "",
                    }
                },
                "gameserver": {
                    "hostname": "gameserver",
                    "dns": [data['dns']],
                    "build": "./game_server",
                    "restart": "unless-stopped",
                    "container_name": g.container_name,
                    "cap_add": [
                        "NET_ADMIN"
                    ],
                    **({
                        "ports": [
                            f"{args.gameserver_port}:80"
                        ]
                    } if args.expose_gameserver else {}),
                    "depends_on": [
                        "router",
                        "database"
                    ],
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
                        "./game_server/checkers/:/app/checkers/:z",
                        "unixsk:/unixsk/:z",
                        "./game_server/config.yml:/app/config.yml:z"
                    ]
                },
                **{
                    f"team{team['id']}": {
                        "hostname": f"team{team['id']}",
                        "dns": [data['dns']],
                        "cap_add": [
                            "CAP_AUDIT_WRITE",
                            "NET_ADMIN",
                            "NET_RAW",
                        ],
                        "security_opt":[
                            "label=disable",
                        ],
                        "build": {
                            "context": "./vm",
                            "args": {
                                "TOKEN": team['token'],
                            }
                        },
                        **({ "storage_opt": {"size":data['max_disk_size']} } if args.disk_limit else {}),
                        "sysctls": [
                            "net.ipv4.ip_unprivileged_port_start=1" #Allow non-privilaged podman to bind all ports
                        ],
                        **({"privileged": "true"} if args.privileged else {}),
                        "restart": "unless-stopped",
                        "devices": [
                            "/dev/fuse",
                            "/dev/net/tun"
                        ],
                        #Allow to edit net.* sysctls (kernel will show only sys option in the network namespace of the container)
                        "volumes": [
                            "/proc/sys/net:/proc/sys/net",
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
                            "NET_ADMIN",
                            "SYS_MODULE"
                        ],
                        "sysctls": [
                            "net.ipv4.ip_forward=1",
                            "net.ipv4.conf.all.src_valid_mark=1",
                        ],
                        "volumes": [
                            f"./wireguard/conf{team['id']}/:/config/:z"
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
                            "PUID": 0,
                            "PGID": 0,
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
                "oasis-postgres-db": ""
            },
            "networks": {
                "externalnet": "",
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
        }))

def try_to_remove(file):
    try:
        os.remove(file)
    except FileNotFoundError:
        pass

def clear_data(
    remove_config=True,
    remove_prebuilded_container=True,
    remove_prebuilder_image=True,
    remove_prebuilt_image=True,
    remove_wireguard=True,
    remove_checkers_data=True,
    remove_gameserver_config=True,
    remove_gameserver_data=True  
):
    if remove_gameserver_data:
        remove_database_volume()
    if remove_wireguard:
        for file in os.listdir("./wireguard"):
            if file.startswith("conf"):
                shutil.rmtree(f"./wireguard/{file}", ignore_errors=True)
    if remove_config:
        try_to_remove(g.config_file)
    if remove_gameserver_config:
        try_to_remove(g.gammeserver_config_file)
    if remove_prebuilded_container:
        remove_prebuilded()
    if remove_prebuilder_image:
        remove_prebuilder()
    if remove_prebuilt_image:
        remove_prebuilt()
    if remove_checkers_data:
        for service in os.listdir("./game_server/checkers"):
            shutil.rmtree(f"./game_server/checkers/{service}/flag_ids", ignore_errors=True)

def clear_data_only(
    remove_config=False,
    remove_prebuilded_container=False,
    remove_prebuilder_image=False,
    remove_prebuilt_image=False,
    remove_wireguard=False,
    remove_checkers_data=False,
    remove_gameserver_config=False,
    remove_gameserver_data=False
):
    clear_data(
        remove_config=remove_config,
        remove_prebuilded_container=remove_prebuilded_container,
        remove_prebuilder_image=remove_prebuilder_image,
        remove_prebuilt_image=remove_prebuilt_image,
        remove_wireguard=remove_wireguard,
        remove_checkers_data=remove_checkers_data,
        remove_gameserver_config=remove_gameserver_config,
        remove_gameserver_data=remove_gameserver_data
    )

def try_mkdir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

def generate_teams_array(number_of_teams: int, enable_nop_team: bool, wireguard_start_port: int):
    teams = []
    for i in range(number_of_teams + (1 if enable_nop_team else 0)):
        team = {
            'id': i,
            'name': f'Team {i}',
            'token': secrets.token_hex(32),
            'wireguard_port': wireguard_start_port+i,
            'nop': False,
            'image': "null"
        }
        if i == 0 and enable_nop_team:
            team['nop'] = True
            team['name'] = 'Nop Team'
        teams.append(team)
    return teams

def config_input():
    data = {}
    if args.privileged:
        puts("Privileged mode enabled (DO NOT USE THIS IN PRODUCTION)", color=colors.yellow)
    while True:
        number_of_teams = int(input('Number of teams: '))
        if number_of_teams < 1:
            print('Number of teams must be greater than 0')
        elif number_of_teams > 250:
            print('Number of teams must be less or equal than 250')
        else:
            break
    if args.wireguard_start_port <= 0:
        print('Wireguard start port must be greater than 0')
        exit(1)
    elif args.wireguard_start_port+number_of_teams > 65535:
        print(f'Wireguard start port must be less or equal than {args.wireguard_start_port+number_of_teams}')
        exit(1)
    data['wireguard_start_port'] = args.wireguard_start_port
    data['dns'] = args.dns
    data['wireguard_profiles'] = args.wireguard_profiles
    data['max_vm_cpus'] = args.max_vm_cpus
    data['max_vm_mem'] = args.max_vm_mem
    data['gameserver_token'] = secrets.token_hex(32)
    data['gameserver_log_level'] = args.gameserver_log_level
    data['flag_expire_ticks'] = args.flag_expire_ticks
    data['initial_service_score'] = args.initial_service_score
    data['max_flags_per_request'] = args.max_flags_per_request
    data['start_time'] = datetime.fromisoformat(args.start_time).isoformat() if args.start_time else None
    data['end_time'] = datetime.fromisoformat(args.end_time).isoformat() if args.end_time else None
    data['submission_timeout'] = args.submission_timeout
    enable_nop_team = input('Enable NOP team? (Y/n): ').lower() != 'n'
    data['server_addr'] = input('Server address: ')
    data['network_limit_bandwidth'] = args.network_limit_bandwidth
    data['max_disk_size'] = args.max_disk_size
    
    while True:
        try:
            data['tick_time'] = abs(int(input('Tick time (s): ')))
            break
        except Exception:
            print('Invalid tick time')
            pass
    data['teams'] = generate_teams_array(number_of_teams, enable_nop_team, args.wireguard_start_port)
    return data

def create_config(data):
    with open(g.config_file, 'w') as f:
        json.dump(data, f, indent=4)
    return data

def config_exists():
    return os.path.isfile(g.config_file)

def read_config():
    with open(g.config_file) as f:
        return json.load(f)

def write_gameserver_config(data):
    nop_team = list(filter(lambda x: x['nop'], data['teams']))
    nop_team = nop_team[0]['id'] if nop_team else None
    gameserver_config = {
        "log_level": data['gameserver_log_level'],
        "round_len": data['tick_time']*1000,
        "token": data['gameserver_token'],
        "nop": f"10.60.{nop_team}.1" if nop_team is not None else "null",
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
        "debug": "false",
    }

    with open(g.gammeserver_config_file, 'w') as f:
        f.write(dict_to_yaml(gameserver_config))
    

def main():
    if not cmd_check("podman --version"):
        puts("Podman not found! please install podman!", color=colors.red)
    if not cmd_check("podman ps"):
        puts("Podman is not running, please install podman and podman compose!", color=colors.red)
        exit()
    elif not cmd_check("podman-compose --version") and not cmd_check("podman compose --version"):
        puts("Podman compose not found! please install podman compose!", color=colors.red)
        exit()
    
    if args.command:
        match args.command:
            case "enable-quotas":
                ask_for_quota_command()
                return
            case "start":
                if check_already_running():
                    puts(f"{g.name} is already running!", color=colors.yellow)
                if args.reset or not config_exists() or args.config_only:
                    config = config_input()
                    create_config(config)
                else:
                    config = read_config()
                if args.config_only:
                    puts(f"Config file generated!, you can customize it by editing {g.config_file}", color=colors.green)
                    return
                write_gameserver_config(config)
                if not prebuilt_exists():
                    if not (args.reset or args.rebuild):
                        puts("Prebuilt image not found!", color=colors.yellow)
                        puts("Clearing old setup images...", color=colors.yellow)
                        #If these images exists, we need to remove them to avoid errors
                        remove_prebuilded()
                        remove_prebuilt()
                    puts("Building the prebuilder image", color=colors.yellow)
                    if not build_prebuilder():
                        puts("Error building prebuilder image", color=colors.red)
                        exit(1)
                    puts("Executing prebuilder to create VMs' base image", color=colors.yellow)
                    if not build_prebuilt():
                        puts("Error building prebuilt image", color=colors.red)
                        exit(1)
                    puts("Creating base VM image (this action can take a while and produces no output)", color=colors.yellow)
                    if not commit_prebuilt():
                        puts("Error commiting prebuilt image", color=colors.red)
                        exit(1)
                    puts("Clear unused images", color=colors.yellow)
                    remove_prebuilded()
                
                if not config_exists():
                    puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                
                else:
                    puts(f"{g.name} is starting!", color=colors.yellow)
                    write_compose(read_config())
                    puts(f"Running 'podman compose up -d{' --build' if use_build_on_compose else ''}'\n", color=colors.green)
                    composecmd(f"up -d{' --build' if use_build_on_compose else ''} --remove-orphans", g.composefile)
            case "compose":
                if not config_exists():
                    puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                else:
                    write_compose(read_config())
                    compose_cmd = " ".join(args.compose_args)
                    puts(f"Running 'podman compose {compose_cmd}'\n", color=colors.green)
                    composecmd(compose_cmd, g.composefile)
            case "restart":
                if not config_exists():
                    puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                elif check_already_running():
                    write_compose(read_config())
                    puts("Running 'podman compose restart'\n", color=colors.green)
                    composecmd("restart", g.composefile)
                else:
                    puts(f"{g.name} is not running!" , color=colors.red, is_bold=True, flush=True)
            case "stop":
                if not config_exists():
                    puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                elif check_already_running():
                    write_compose(read_config())
                    puts("Running 'podman compose down'\n", color=colors.green)
                    composecmd("down --remove-orphans", g.composefile)
                else:
                    puts(f"{g.name} is not running!" , color=colors.red, is_bold=True, flush=True)
            case "clear":
                if check_already_running():
                    puts(f"{g.name} is running! please stop it before clearing the data", color=colors.red)
                    exit(1)
                if args.all:
                    puts("This will clear everything, EVEN THE CONFIG JSON, are you sure? (y/N): ", end="")
                    if input().lower() != 'y':
                        return
                    puts("Clearing everything (even config!!)", color=colors.yellow)
                    clear_data()
                if args.config:
                    clear_data_only(remove_config=True)
                if args.prebuilded_container:
                    clear_data_only(remove_prebuilded_container=True)
                if args.prebuilder_image:
                    clear_data_only(remove_prebuilder_image=True)
                if args.prebuilt_image:
                    clear_data_only(remove_prebuilt_image=True)
                if args.wireguard:
                    clear_data_only(remove_wireguard=True)
                if args.checkers_data:
                    clear_data_only(remove_checkers_data=True)
                if args.gameserver_config:
                    clear_data_only(remove_gameserver_config=True)
                if args.gameserver_data:
                    clear_data_only(remove_gameserver_data=True)
                puts("Whatever you specified has been cleared!", color=colors.green, is_bold=True)

    
    if "logs" in args and args.logs:
        if config_exists():
            write_compose(read_config())
        else:
            puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
        composecmd("logs -f")


if __name__ == "__main__":
    try:
        try:
            main()
        finally:
            kill_builder()
            if os.path.isfile(g.composefile) and not g.keep_file:
                os.remove(g.composefile)
    except KeyboardInterrupt:
        print()

