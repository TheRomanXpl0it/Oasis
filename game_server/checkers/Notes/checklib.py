import sys
from enum import Enum
import requests
import os, hashlib, json

TOKEN = os.getenv("TOKEN")

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('flag_ids', exist_ok=True)

class Status(Enum):
    OK = 101
    DOWN = 104
    ERROR = 110


class Action(Enum):
    CHECK_SLA = 'CHECK_SLA'
    PUT_FLAG = 'PUT_FLAG'
    GET_FLAG = 'GET_FLAG'

    def __str__(self):
        return str(self.value)

def save_flag_data(flag:str, data):
    with open(f'flag_ids/flag_{hashlib.sha256(flag.encode()).hexdigest()}.txt', 'w') as f:
        f.write(json.dumps(data))

def get_flag_data(flag:str):
    with open(f'flag_ids/flag_{hashlib.sha256(flag.encode()).hexdigest()}.txt', 'r') as f:
        return json.loads(f.read())

def get_data():
    data = {
        'action': os.environ['ACTION'],
        'teamId': os.environ['TEAM_ID'],
        'round': os.environ['ROUND']
    }

    if data['action'] == Action.PUT_FLAG.name or data['action'] == Action.GET_FLAG.name:
        data['flag'] = os.environ['FLAG']

    return data


def quit(exit_code, comment='', debug=''):
    if isinstance(exit_code, Status):
        exit_code = exit_code.value

    print(debug)
    print(comment, file=sys.stderr)
    exit(exit_code)


def post_flag_id(service_id, team_id, flag_id):
    requests.post('http://flagid:8081/postFlagId', json={
        'token': TOKEN,
        'serviceId': service_id,
        'teamId': team_id,
        'round': int(os.environ['ROUND']),
        'flagId': flag_id
    })
