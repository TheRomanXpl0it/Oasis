#!/usr/bin/env python3

import binascii
from binascii import unhexlify, hexlify
from pwn import *

from Crypto.PublicKey import RSA
from Crypto.Cipher import DES
from Crypto.Util.number import long_to_bytes, bytes_to_long
from hashlib import sha256
import random
from crypto import decrypt, encrypt, sign, verify
import os

import checklib

data = checklib.get_data()
action = data['action']
team_id = data['teamId']
round = int(data['round'])

service_addr = '10.60.' + team_id + '.1'
service_name = 'Crystore'
port = 9122 

if 'flag' in data:
	flag = data['flag']
	flag_id = sha256(flag.encode()).hexdigest()[:20]

os.makedirs('flag_ids', exist_ok=True)


private_key = RSA.importKey(open('checker.privkey','r').read())


def connect():
	try:
		r = remote(service_addr, port)
		r.recvuntil(b'command: ')
		return r
	except EOFError:
		checklib.quit(checklib.Status.DOWN, "EOFError")

def get_pubkey():
	conn = connect()
	conn.sendlineafter('command: ', b'send_pubkey', timeout=1)
	pubkey = conn.recvuntil('-----END PUBLIC KEY-----\n').strip().decode()
	conn.close()
	return RSA.import_key(pubkey)

def put_flag():
	try:
		pubkey = get_pubkey()
		content = 'flag %s %d' % (encrypt(flag, pubkey), round)
		signature = sign(content, private_key)

		input_data = ('store %s %s' % (content, signature)).encode()
		conn = connect()
		conn.sendline(input_data)
		try:
			ret = conn.recvline().decode().strip().split(":")
			ret_hash = ret[0]
			ret_id = ret[1]

		except IndexError:
			conn.close()
			checklib.quit(checklib.Status.DOWN, "Failed to parse hash")

		conn.close()

		if sha256(flag.encode()).hexdigest() != ret_hash.strip():
			checklib.quit(checklib.Status.DOWN, 'Returned wrong hash')

		with open(f'flag_ids/{ret_hash[:20]}{team_id}{round}', 'w') as f:
			f.write(ret_id)
		checklib.post_flag_id(service_name, team_id, ret_id)
		
	except EOFError:
		checklib.quit(checklib.Status.DOWN, "Encountered unexpected EOF")
	except UnicodeError:
		checklib.quit(checklib.Status.DOWN, "Fucked UTF8")
	except Exception as e:
		checklib.quit(checklib.Status.DOWN, str(e))
	
	checklib.quit(checklib.Status.OK)

def get_flag():
	try:
		conn = connect()
		with open(f'flag_ids/{flag_id}{team_id}{round}', 'r') as f:
			flag_n = int(f.read())
		conn.sendline(f"load {flag_n}".encode())
		ciphertext = conn.recvline().decode().strip()
		conn.close()
		try:
			flag_dec = decrypt(ciphertext, privkey = private_key)
		except Exception:
			checklib.quit(checklib.Status.DOWN, "Flag-Decryption failed")

		if not flag_dec == flag:
			checklib.quit(checklib.Status.DOWN, "Resulting flag was found to be incorrect")
	except EOFError:
		raise checklib.quit(checklib.Status.DOWN, "Encountered unexpected EOF")
	except UnicodeError:
		checklib.quit(checklib.Status.DOWN, "Fucked UTF8")
	except Exception as e:
		checklib.quit(checklib.Status.DOWN, str(e))
	
	checklib.quit(checklib.Status.OK)

def putnoise():
	try:
		joke = random.choice(open('jokes','r').read().split('\n\n'))
		joke_hex = hexlify(joke.encode()).decode()

		content = 'joke %s %d' % (joke_hex, round)
		signature = sign(content, private_key)

		input_data = ('store %s %s' % (content, signature)).encode()

		conn = connect()
		conn.sendline(input_data)

		try:
			ret = conn.recvline().decode().strip().split(":")
			ret_hash = ret[0]
			ret_id = ret[1]
			with open(f'flag_ids/{ret_hash[:20]}{team_id}{round}', 'w') as f:
				f.write(ret_id)
		except IndexError:
			conn.close()
			checklib.quit(checklib.Status.ERROR, "Failed to parse hash")

		conn.close()

		if sha256(joke.encode()).hexdigest() != ret_hash.strip():
			print(sha256(joke.encode()).hexdigest())
			print(ret_hash.strip())
			checklib.quit(checklib.Status.DOWN, 'Returned wrong hash')

	except Exception as e:
		checklib.quit(checklib.Status.DOWN, str(e))

def check_sla():
	putnoise()
	checklib.quit(checklib.Status.OK)


def main():
	if action == checklib.Action.CHECK_SLA.name:
		check_sla()
	elif action == checklib.Action.PUT_FLAG.name:
		put_flag()
	elif action == checklib.Action.GET_FLAG.name:
		get_flag()

if __name__ == "__main__":
    main()