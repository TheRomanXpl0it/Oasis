#!/usr/bin/env python3

import requests
import random
import string
import time

from bs4 import BeautifulSoup
import checklib
from hashlib import sha256
import os


data = checklib.get_data()
action = data['action']
team_id = data['teamId']
round = int(data['round'])
if 'flag' in data:
    flag = data['flag']

service_addr = '10.60.' + team_id + '.1'
#service_addr = 'localhost'
service_name = 'sesame'

os.makedirs('flag_keys', exist_ok=True)


def check_sla():
    rand_key = ''.join(random.choice(string.ascii_uppercase) for _ in range(32))
    print(rand_key)
    url = "http://" + service_addr + ":4280/" + rand_key
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, features="html.parser")
        key = soup.find(id="key").text
        if key == rand_key:
            checklib.quit(checklib.Status.OK, "Service is up!")
        print("Expected to find random key " + rand_key + "on the page, but found " + key)
        checklib.quit(checklib.Status.DOWN, "Front page is broken!")
    except Exception as e:
        print(e)
        checklib.quit(checklib.Status.DOWN, "Couldn't get a meaningful response!")


def put_flag():
    url = "http://" + service_addr + ":4280/"
    try:
        for i in range(3):
            response = requests.post(url, data = { "secret": flag[:31] }, allow_redirects = False)
            key = response.headers['Location'][1:]
            if len(key) == 0:
                print("Couldn't get flag id. Response was: ", vars(response))
                time.sleep(i + 1)
                continue
            with open('flag_keys/'+flag[:31], 'w') as f:
                f.write(key)
            print("Saved flag " + flag)
            print("With key " + key)
            checklib.quit(checklib.Status.OK)
        checklib.quit(checklib.Status.DOWN, "Couldn't put flag!")
    except Exception as e:
        print(e)
        checklib.quit(checklib.Status.DOWN, "Couldn't get a meaningful response!")


def get_flag():
    with open('flag_keys/'+flag[:31], 'r') as f:
        flag_id = f.read()

    url = "http://" + service_addr + ":4280/" + flag_id
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, features="html.parser")
        secret = soup.find(id="secret").text
        if secret + "=" == flag:
            checklib.quit(checklib.Status.OK)
        if secret == '':
            print("Flag is missing for id = " + flag_id)
            checklib.quit(checklib.Status.DOWN, "Flag is missing!")
        print("Flag value mismatch for id = " + flag_id + ". Got " + secret +
            ", wanted " + flag)
        checklib.quit(checklib.Status.DOWN, "Flag value mismatch!")
    except Exception as e:
        print(e)
        checklib.quit(checklib.Status.DOWN, "Couldn't get a meaningful response!")


def main():
	if action == checklib.Action.CHECK_SLA.name:
		check_sla()
	elif action == checklib.Action.PUT_FLAG.name:
		put_flag()
	elif action == checklib.Action.GET_FLAG.name:
		get_flag()

if __name__ == "__main__":
    main()

    