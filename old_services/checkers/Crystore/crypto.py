#!/usr/bin/env python3

from binascii import unhexlify, hexlify
from Crypto.Util.number import bytes_to_long, long_to_bytes
from Crypto.Cipher import DES
from hashlib import sha256
import os

def pad(message : str, size = 8) -> bytes:
	message = message.encode()
	post = long_to_bytes(len(message))
	return message + b'\x00' * (size - (len(message + post) % size)) + post

def unpad(message : bytes) -> str:
	i = -1
	while message[i]: i -= 1
	l = bytes_to_long(message[i:])
	return message[:l].decode()

def decrypt(ciphertext : str, key : str = None, privkey = None) -> str:
	if key is None:
		if ciphertext.count(':') != 1:
			raise Exception('invalid input for decryption')
		ciphertext, key = ciphertext.split(':')
	if privkey is not None:
		key = long_to_bytes(pow(int(key,16), privkey.d, privkey.n))
		key = b'\x00' * (14 - len(key)) + key
	else:
		key = unhexlify(key)
	key1 = key[-14:-7]
	key2 = key[-7:]

	cipher1 = DES.new(b'\x00' + key1, DES.MODE_ECB)
	cipher2 = DES.new(b'\x00' + key2, DES.MODE_ECB)
	#decode the flag with triple-DES
	message = cipher1.decrypt(cipher2.encrypt(cipher1.decrypt(unhexlify(ciphertext))))
	return unpad(message)

def encrypt(message : str, pubkey = None):
	key1 = os.urandom(7)	
	key2 = os.urandom(7)	
	cipher1 = DES.new(b'\x00' + key1, DES.MODE_ECB)
	cipher2 = DES.new(b'\x00' + key2, DES.MODE_ECB)
	# padding
	message = pad(message)
	# encode the flag with triple-DES
	enc_flag = hexlify(cipher1.encrypt(cipher2.decrypt(cipher1.encrypt(message)))).decode()
	key = key1 + key2
	if pubkey is not None:
		rsapad = b"" * 100
		enc_key = hex(pow(bytes_to_long(rsapad + key), pubkey.e, pubkey.n))[2:]
	else:
		enc_key = hexlify(key).decode()
	return '%s:%s' % (enc_flag, enc_key)

def sign(message: str, RSAkey):
	return hex(pow(bytes_to_long(sha256(message.encode()).digest()), RSAkey.d, RSAkey.n))[2:]

def verify(message: str, signature: str, RSAkey):
	return bytes_to_long(sha256(message.encode()).digest()) == pow(int(signature, 16), RSAkey.e, RSAkey.n)

