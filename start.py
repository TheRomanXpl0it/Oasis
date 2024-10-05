#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys, os, subprocess
import json, secrets, shutil, time
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
    gammeserver_config_file = "game_server/src/config.yml"
    prebuild_image = "oasis-prebuilder"
    prebuilded_container = "oasis-prebuilded"
    prebuilt_image = "oasis-vm-base"

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

def puts(text, *args, color=colors.white, is_bold=False, **kwargs):
    print(f'{pref}{1 if is_bold else 0};{color}' + text + reset, *args, **kwargs)

def sep(): puts("-----------------------------------", is_bold=True)

def check_if_exists(program, get_output=False, print_output=False, no_stderr=False):
    if get_output:
        return subprocess.getoutput(program)
    if print_output:
        return subprocess.call(program, shell=True) == 0
    return subprocess.call(program, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL if no_stderr else subprocess.STDOUT, shell=True) == 0

def composecmd(cmd, composefile=None):
    if composefile:
        cmd = f"-f {composefile} {cmd}"
    if not check_if_exists("docker ps"):
        return puts("Cannot use docker, the user hasn't the permission or docker isn't running", color=colors.red)
    elif check_if_exists("docker compose"):
        return os.system(f"docker compose -p {g.compose_project_name} {cmd}")
    elif check_if_exists("docker-compose"):
        return os.system(f"docker-compose -p {g.compose_project_name} {cmd}")
    else:
        puts("Docker compose not found! please install docker compose!", color=colors.red)

def dockercmd(cmd):
    if check_if_exists("docker"):
        return os.system(f"docker {cmd}")
    elif not check_if_exists("docker ps"):
        puts("Cannot use docker, the user hasn't the permission or docker isn't running", color=colors.red)
    else:
        puts("Docker not found! please install docker!", color=colors.red)

def check_already_running():
    return g.container_name in check_if_exists(f'docker ps --filter "name=^{g.container_name}$"', get_output=True)

def prebuilder_exists():
    return g.prebuild_image in check_if_exists(f'docker image ls --filter "reference={g.prebuild_image}"', get_output=True)

def prebuilt_exists():
    return g.prebuilt_image in check_if_exists(f'docker image ls --filter "reference={g.prebuilt_image}"', get_output=True)

def remove_prebuilder():
    return check_if_exists(f'docker image rm {g.prebuild_image}')

def remove_prebuilt():
    return check_if_exists(f'docker image rm {g.prebuilt_image}')

def remove_prebuilded():
    return check_if_exists(f'docker container rm {g.prebuilded_container}')

def build_prebuilder():
    return check_if_exists(f'docker build -t {g.prebuild_image} -f ./vm/Dockerfile.prebuilder ./vm/', print_output=True)

def build_prebuilt():
    return check_if_exists(f'docker run -it --privileged --name {g.prebuilded_container} {g.prebuild_image}', print_output=True)

def kill_builder():
    return check_if_exists(f'docker kill {g.prebuilded_container}', no_stderr=True)

def commit_prebuilt():
    return check_if_exists(f'docker commit {g.prebuilded_container} {g.prebuilt_image}', print_output=True)

def gen_args(args_to_parse: list[str]|None = None):                     
    
    #Main parser
    parser = argparse.ArgumentParser(description=f"{g.name} Manager")
    
    parser.add_argument('--clear', dest="bef_clear", required=False, action="store_true", help=f'Delete volumes folder associated to {g.name} and oasis json config', default=False)

    subcommands = parser.add_subparsers(dest="command", help="Command to execute", required=True)
    
    #Compose Command
    parser_compose = subcommands.add_parser('compose', help='Run docker compose command')
    parser_compose.add_argument('compose_args', nargs=argparse.REMAINDER, help='Arguments to pass to docker compose', default=[])
    
    #Start Command
    parser_start = subcommands.add_parser('start', help=f'Start {g.name}')
    parser_start.add_argument('--logs', required=False, action="store_true", help=f'Show {g.name} logs', default=False)
    parser_start.add_argument('--reset', required=False, action="store_true", help=f'Regenerate VM base image and configuration', default=False)
    parser_start.add_argument('--rebuild-vm', required=False, action="store_true", help=f'Rebuild VM base image', default=False)
    #Gameserve options
    parser_start.add_argument('--wireguard-start-port', type=int, default=51000, help='Wireguard start port')
    parser_start.add_argument('--gameserver-log-level', default="info", help='Log level for game server')
    parser_start.add_argument('--max-vm-mem', type=str, default="2G", help='Max memory for VMs')
    parser_start.add_argument('--max-vm-cpus', type=str, default="1", help='Max CPUs for VMs')
    parser_start.add_argument('--wireguard-profiles', type=int, default=10, help='Number of wireguard profiles')
    parser_start.add_argument('--dns', type=str, default="1.1.1.1", help='DNS server')
    parser_start.add_argument('--submission-timeout', type=int, default=10, help='Submission timeout rate limit')
    parser_start.add_argument('--flag-expire-ticks', type=int, default=5, help='Flag expire ticks')
    parser_start.add_argument('--initial-service-score', type=int, default=5000, help='Initial service score')
    parser_start.add_argument('--max-flags-per-request', type=int, default=2000, help='Max flags per request')
    parser_start.add_argument('--start-time', type=str, help='Start time (ISO 8601)')
    parser_start.add_argument('--end-time', type=str, help='End time (ISO 8601)')
    #init options
    parser_start.add_argument('--privileged', '-P', action='store_true', help='Use privileged mode for VMs')
    parser_start.add_argument('--debug', '-D', action='store_true', help='Debug mode')
    parser_start.add_argument('--config-only', '-C', action='store_true', help='Only generate config file')


    #Stop Command
    parser_stop = subcommands.add_parser('stop', help=f'Stop {g.name}')
    parser_stop.add_argument('--clear', required=False, action="store_true", help=f'Delete docker volume associated to {g.name} resetting all the settings', default=False)
    
    parser_restart = subcommands.add_parser('restart', help=f'Restart {g.name}')
    parser_restart.add_argument('--logs', required=False, action="store_true", help=f'Show {g.name} logs', default=False)
    parser_restart.add_argument('--privileged', '-P', action='store_true', help='Use privileged mode for VMs')
    parser_restart.add_argument('--debug', '-D', action='store_true', help='Debug mode')
    
    args = parser.parse_args(args=args_to_parse)
    
    if not "clear" in args:
        args.clear = False
        
    if not "debug" in args:
        args.debug = False

    if not "privileged" in args:
        args.privileged = False
        
    args.clear = args.bef_clear or args.clear

    return args

args = gen_args()

def write_compose(data):
    with open(g.composefile,"wt") as compose:
        compose.write(dict_to_yaml({
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
                    "image": "postgres:17",
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
                    "container_name": g.container_name,
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
                        **({"privileged": "true"} if args.privileged else { "runtime": "sysbox-runc" }),
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
    remove_gameserver_data=True,
    remove_vm_data=True,
    
):
    if remove_vm_data and remove_gameserver_data:
        shutil.rmtree("./volumes", ignore_errors=True)
    elif remove_vm_data:
        for folder in os.listdir("./volumes"):
            if folder.startswith("team"):
                shutil.rmtree(f"./volumes/{folder}", ignore_errors=True)
    elif remove_gameserver_data:
        shutil.rmtree("./volumes/database", ignore_errors=True)
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

def config_input():
    data = {}
    if args.privileged:
        puts("Privileged mode enabled (DO NOT USE THIS IN PRODUCTION)", color=colors.yellow)
    else:
        puts("To run this project you need to install sysbox! https://github.com/nestybox/sysbox if your VM will be given to trusted people and can't install sysbox, use --privileged", color=colors.yellow)
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
    data['enable_nop_team'] = input('Enable NOP team? (Y/n): ').lower() != 'n'
    data['server_addr'] = input('Server address: ')
    
    while True:
        try:
            data['tick_time'] = abs(int(input('Tick time (s): ')))
            break
        except Exception:
            print('Invalid tick time')
            pass
    data['teams'] = generate_teams_array(data)
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

    with open(g.gammeserver_config_file, 'w') as f:
        f.write(dict_to_yaml(gameserver_config))


def main():    
    if not check_if_exists("docker"):
        puts("Docker not found! please install docker and docker compose!", color=colors.red)
        exit()
    elif not check_if_exists("docker-compose") and not check_if_exists("docker compose"):
        puts("Docker compose not found! please install docker compose!", color=colors.red)
        exit()
    if not check_if_exists("docker ps"):
        puts("Cannot use docker, the user hasn't the permission or docker isn't running", color=colors.red)
        exit()    
    
    if args.command:
        match args.command:
            case "start":
                if check_already_running():
                    puts(f"{g.name} is already running! use --help to see options useful to manage {g.name} execution", color=colors.yellow)
                else:
                    if args.reset or not config_exists() or args.config_only:
                        config = config_input()
                        create_config(config)
                    else:
                        config = read_config()
                    if args.config_only:
                        puts(f"Config file generated!, you can customize editing {g.config_file}", color=colors.green)
                        return
                    if args.reset or args.rebuild_vm:
                        puts("Clearing old setup images and volumes", color=colors.yellow)
                        clear_data(remove_config=False)
                    write_gameserver_config(config)
                    if not prebuilt_exists():
                        if not (args.reset or args.rebuild_vm):
                            puts("Prebuilt image not found!", color=colors.yellow)
                            puts("Clearing old setup images...", color=colors.yellow)
                            #If these images exists, we need to remove them to avoid errors
                            remove_prebuilder()
                            remove_prebuilded()
                            remove_prebuilt()
                        puts("Building the prebuilder image", color=colors.yellow)
                        if not build_prebuilder():
                            puts("Error building prebuilder image", color=colors.red)
                            exit(1)
                        puts("Executing prebuilder to creating VMs base image", color=colors.yellow)
                        if not build_prebuilt():
                            puts("Error building prebuilt image", color=colors.red)
                            exit(1)
                        puts("Creating base VM image (this action takes time and gives no output)", color=colors.yellow)
                        if not commit_prebuilt():
                            puts("Error commiting prebuilt image", color=colors.red)
                            exit(1)
                        puts("Clear unused images", color=colors.yellow)
                        remove_prebuilder()
                        remove_prebuilded()
                    
                    if not config_exists():
                        puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                    
                    else:
                        puts(f"{g.name} is starting!", color=colors.yellow)
                        write_compose(read_config())
                        puts("Running 'docker compose up -d --build'\n", color=colors.green)
                        composecmd("up -d --build", g.composefile)
            case "compose":
                if not config_exists():
                    puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                else:
                    write_compose(read_config())
                    compose_cmd = " ".join(args.compose_args)
                    puts(f"Running 'docker compose {compose_cmd}'\n", color=colors.green)
                    composecmd(compose_cmd, g.composefile)
            case "restart":
                if not config_exists():
                    puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                elif check_already_running():
                    write_compose(read_config())
                    puts("Running 'docker compose restart'\n", color=colors.green)
                    composecmd("restart", g.composefile)
                else:
                    puts(f"{g.name} is not running!" , color=colors.red, is_bold=True, flush=True)
            case "stop":
                if not config_exists():
                    puts(f"Config file not found! please run {sys.argv[0]} start", color=colors.red)
                elif check_already_running():
                    write_compose(read_config())
                    puts("Running 'docker compose down'\n", color=colors.green)
                    composecmd("down", g.composefile)
                else:
                    puts(f"{g.name} is not running!" , color=colors.red, is_bold=True, flush=True)
    

    
    if args.clear:
        if check_already_running():
            puts(f"{g.name} is running! please stop it before clear the data", color=colors.red)
            exit(1)
        clear_data()
        puts(f"Volumes and config clean!", color=colors.green, is_bold=True)

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

