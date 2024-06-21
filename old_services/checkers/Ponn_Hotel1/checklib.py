import sys
from enum import Enum
import requests
import os

TOKEN = os.getenv("TOKEN", "5d46276c259b7fa846b6d2ed6d575e6b")


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


def get_data():
    data = {
        'action': os.environ['ACTION'],
        'teamId': os.environ['TEAM_ID'],
        'round': os.environ['ROUND']
    }

    data['flag'] = os.environ['FLAG']

    return data


def quit(exit_code, comment='', debug=''):
    if isinstance(exit_code, Status):
        exit_code = exit_code.value

    print(comment)
    print(debug, file=sys.stderr)
    exit(exit_code)


def post_flag_id(service_id, team_id, flag_id):
    requests.post('http://flagid:8081/postFlagId', json={
        'token': TOKEN,
        'serviceId': service_id,
        'teamId': team_id,
        'round': int(os.environ['ROUND']),
        'flagId': flag_id
    })
