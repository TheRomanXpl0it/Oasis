#!/usr/bin/env python3

import hashlib
import os
import random
import string

import requests
import bs4
from pwn import *


import checklib
from hashlib import sha256

data = checklib.get_data()
action = data['action']
team_id = data['teamId']
service_addr = '10.60.' + team_id + '.1'
service_name = 'ponn_hotel_2'

os.makedirs('flag_ids', exist_ok=True)


def register_user(username, password, flag, pin):
    try:
        p = process("./ponn_hotel")
        p.recvuntil(b">", timeout=1)
        p.sendline(b"1")
        p.recvuntil(b">", timeout=1)
        p.sendline(username.encode())
        p.recvuntil(b">", timeout=1)
        p.sendline(password.encode())
        received = p.recvline()
        if (received != b"Welcome "+username.encode()+b"!\n"):
            checklib.quit(checklib.Status.DOWN)
        p.recvuntil(b">", timeout=0.1)
        p.sendline(b"2")
        p.recvuntil(b">", timeout=1)
        p.sendline(flag.encode())
        p.recvuntil(b">", timeout=1)
        p.sendline(pin.encode())
        received = p.recvuntil(b">", timeout=1)
        print(received)
        if (b"What do you want to do?" in received):
            return
        checklib.quit(checklib.Status.DOWN)
    except Exception as e:
        print(e)
        checklib.quit(checklib.Status.DOWN)


def login_user(username, password):
    try:
        p = process("./ponn_hotel")
        p.recvuntil(b">", timeout=1)
        p.sendline(b"2")
        p.recvuntil(b">", timeout=1)
        p.sendline(username.encode())
        p.recvuntil(b">", timeout=1)
        p.sendline(password.encode())
        received = p.recvline()
        if (received == b"Welcome "+username.encode()+b"!\n"):
            return
        checklib.quit(checklib.Status.DOWN)
    except Exception as e:
        print(e)
        checklib.quit(Checklib.Status.DOWN)


def check_credit_card(username, password, flag, pin):
    try:
        p = process(b"./ponn_hotel")
        p.recvuntil(b">", timeout=1)
        p.sendline(b"2")
        p.recvuntil(b">", timeout=1)
        p.sendline(username.encode())
        p.recvuntil(b">", timeout=1)
        p.sendline(password.encode())
        p.recvuntil(b">", timeout=1)
        p.sendline(b"2")
        p.recvuntil(b">", timeout=1)
        p.sendline(flag.encode())
        p.recvuntil(b">", timeout=1)
        p.sendline(pin.encode())
        received = p.recvuntil(b">", timeout=1)
        if (b"You got some credit card already in pipe, please wait for your previous request to be accepted." not in received):
            checklib.quit(checklib.Status.DOWN)
        p.sendline(b"1")
        p.recvuntil(b">", timeout=1)
        p.sendline(pin.encode())
        received = p.recvuntil(b">", timeout=1)
        if (flag.encode() not in received):
            checklib.quit(checklib.Status.DOWN)
    except Exception as e:
        print(e)
        checklib.quit(checklib.Status.DOWN)
    return


def check_sla():
    flag = data['flag']
    username = sha256(flag.encode()).hexdigest()[:15]
    password = sha256(flag[:-1].encode()).hexdigest()[:15]
    login_user(username, password)
    checklib.quit(checklib.Status.OK)


def put_flag():
    flag = data['flag']
    username = sha256(flag.encode()).hexdigest()[:15]
    password = sha256(flag[:-1].encode()).hexdigest()[:15]
    pin = flag[:3]
    checklib.post_flag_id(service_name, team_id, username)
    register_user(username, password, flag, pin)
    checklib.quit(checklib.Status.OK)


def get_flag():
    flag = data['flag']
    username = sha256(flag.encode()).hexdigest()[:15]
    password = sha256(flag[:-1].encode()).hexdigest()[:15]
    pin = flag[:3]
    check_credit_card(username, password, flag, pin)
    checklib.quit(checklib.Status.OK)


def main():
    try:
        if action == checklib.Action.CHECK_SLA.name:
            check_sla()
        elif action == checklib.Action.PUT_FLAG.name:
            put_flag()
        elif action == checklib.Action.GET_FLAG.name:
            get_flag()
    except requests.RequestException as e:
        checklib.quit(checklib.Status.DOWN, 'Request error', str(e))


if __name__ == "__main__":
    main()
