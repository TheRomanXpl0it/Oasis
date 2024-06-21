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
service_name = 'Ponn_Hotel1'
port = 1337

os.makedirs('flag_ids', exist_ok=True)


def register_user(username, password, flag):
	try:
		# p = process("./ponn_hotel")
		p = remote(service_addr, port)
		p.recvuntil(b">", timeout=1)
		p.sendline(b"1")
		p.recvuntil(b">", timeout=1)
		p.sendline(username.encode())
		p.recvuntil(b">", timeout=1)
		p.sendline(password.encode())
		received = p.recvline()
		print(received)
		if (received != b"Welcome "+username.encode()+b"!\n"):
			checklib.quit(checklib.Status.DOWN)
		p.recvuntil(b">", timeout=0.1)
		p.sendline(b"1")
		room = random.randint(0, 255)
		p.recvuntil(b">", timeout=0.1)
		p.sendline(str(room).encode())
		day = random.randint(1, 25)
		month = random.randint(1, 12)
		year = random.randint(2024, 2025)
		date = str(day).encode() + b'/'+str(month).encode() + b"/" + str(year).encode() + \
			b"-" + str(day+1).encode() + b"/" + \
			str(month).encode() + b"/" + str(year).encode()
		p.sendline(date)
		p.recvuntil(b"Got any notes? >", timeout=1)
		p.sendline(flag.encode())
		received = p.recvuntil("What do you want to do?", timeout=1)
		if (received == b"What do you want to do?"):
			return
		checklib.quit(checklib.Status.DOWN)
	except Exception as e:
		print(e)
		checklib.quit(checklib.Status.DOWN)


def login_user(username, password):
	try:
		p = remote(service_addr, port)
		p.recvuntil(b">", timeout=1)
		p.sendline(b"2")
		p.recvuntil(b">", timeout=1)
		p.sendline(username.encode())
		p.recvuntil(b">", timeout=1)
		p.sendline(password.encode())
		received = p.recvline(timeout=1)
		if (received == b"Welcome "+username.encode()+b"!\n"):
			return
		checklib.quit(checklib.Status.DOWN)
	except Exception as e:
		print(e)
		checklib.quit(Checklib.Status.DOWN)


def check_reservation(username, password, flag):
	try:
		p = remote(service_addr, port)
		p.recvuntil(b">", timeout=1)
		p.sendline(b"2")
		p.recvuntil(b">", timeout=1)
		p.sendline(username.encode())
		p.recvuntil(b">", timeout=1)
		p.sendline(password.encode())
		p.recvuntil(b">", timeout=1)
		p.sendline(b"3")
		reservations = p.recvuntil(b">", timeout=1)
		print(reservations)
		print(flag.encode())
		if (flag.encode() not in reservations):
			checklib.quit(checklib.Status.DOWN)
	except Exception as e:
		print(e)
		checklib.quit(checklib.Status.DOWN)
	return


def check_sla():
	try:
		p = remote(service_addr, port)
		checklib.quit(checklib.Status.OK)
	except Exception as e:
		checklib.quit(checklib.Status.DOWN, e)

def put_flag():
	flag = data['flag']
	username = sha256(flag.encode()).hexdigest()[:15]
	password = sha256(flag[:-1].encode()).hexdigest()[:15]
	checklib.post_flag_id(service_name, team_id, username)
	register_user(username, password, flag)
	checklib.quit(checklib.Status.OK)


def get_flag():
	flag = data['flag']
	username = sha256(flag.encode()).hexdigest()[:15]
	password = sha256(flag[:-1].encode()).hexdigest()[:15]
	check_reservation(username, password, flag)
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
