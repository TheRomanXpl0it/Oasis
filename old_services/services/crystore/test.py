import random
import string
from Crypto.PublicKey import RSA
from hashlib import sha256
from binascii import unhexlify, hexlify

from cry import Store
from crypto import pad, unpad, decrypt, encrypt, sign, verify

# testing crypto

def test_padding():
	for size in range(8,17):
		for str_len in range(0,12):
			s = ''.join([random.choice(string.printable) for _ in range(str_len)])
			padded = pad(s, size = size)
			assert len(padded) % size == 0
			unpadded = unpad(padded)
			assert unpadded == s

def test_encrypt_nokey():
	for str_len in range(5,12):
		message = 'ENO{%s}' % ''.join([random.choice(string.printable[:95]) for _ in range(str_len)])
		ciphertext = encrypt(message)
		test_message = decrypt(ciphertext)
		assert message == test_message

def test_encrypt_key():
	for _ in range(5):
		privkey = RSA.generate(2048)
		pubkey = privkey.publickey()
		for str_len in range(2,20):
			for _ in range(10):
				message = 'ENO{%s}' % ''.join([random.choice(string.printable[:95]) for _ in range(str_len)])
				ciphertext = encrypt(message, pubkey)
				test_message = decrypt(ciphertext, privkey = privkey)
				assert message == test_message

def test_sign():
	for _ in range(5):
		privkey = RSA.generate(2048)
		pubkey = privkey.publickey()
		for str_len in range(2,200):
			message = 'ENO{%s}' % ''.join([random.choice(string.printable[:95]) for _ in range(str_len)])
			signature = sign(message, privkey)
			assert verify(message, signature, pubkey)

# testing service

def test_get_pubkey():
	service = Store()
	command = 'send_pubkey'
	res = service.process_command(command.encode())
	pubkey = RSA.import_key(res)

def test_store_get_joke():
	service = Store()
	for _ in range(5):
		tick = random.randint(1, 1<<32)
		joke = 'Why did the fly fly? Because the spider spied \'er.'
		res = service.handle_store('joke', hexlify(joke.encode()).decode(), str(tick))
		assert res == sha256(joke.encode()).hexdigest()
		res = service.handle_load('joke', tick)
		assert joke == unhexlify(res).decode()

def test_store_get_flag():
	service = Store()
	pubkey = RSA.import_key(service.process_command('send_pubkey'.encode()))
	privkey = RSA.import_key(open('../checker/checker.privkey','r').read())
	for str_len in range(2,20):
		tick = random.randint(1, 1<<32)
		flag = 'ENO{%s}' % ''.join([random.choice(string.printable[:95]) for _ in range(str_len)])

		data = encrypt(flag, pubkey)

		res = service.handle_store('flag', data, str(tick))
		assert res == sha256(flag.encode()).hexdigest()
		res = service.handle_load('flag', tick)
		test_flag = decrypt(service.handle_load('flag',tick), privkey = privkey)
		assert test_flag == flag

def test_command_flag():
	service = Store()
	pubkey = RSA.import_key(service.process_command('send_pubkey'.encode()))
	privkey = RSA.import_key(open('../checker/checker.privkey','r').read())
	for str_len in range(2,20):
		tick = random.randint(1, 1<<32)
		flag = 'ENO{%s}' % ''.join([random.choice(string.printable[:95]) for _ in range(str_len)])

		data = encrypt(flag, pubkey)
		content = 'flag %s %d' % (data, tick)
		res = service.process_command(('store %s %s' % (content, sign(content, privkey))).encode())
		assert res == sha256(flag.encode()).hexdigest()

		input_command = ('load flag %d' % tick).encode()
		res = service.process_command(input_command)
		test_flag = decrypt(res, privkey = privkey)
		assert test_flag == flag
		
def test_command_joke():
	service = Store()
	pubkey = RSA.import_key(service.process_command('send_pubkey'.encode()))
	privkey = RSA.import_key(open('../checker/checker.privkey','r').read())
	tick = random.randint(1, 1<<32)
	joke = 'How do you call a fly without wings? - A walk.'

	content = 'joke %s %d' % (hexlify(joke.encode()).decode(), tick)
	res = service.process_command(('store %s %s' % (content, sign(content, privkey))).encode())
	assert res == sha256(joke.encode()).hexdigest()

	input_command = ('load joke %d' % tick).encode()
	res = service.process_command(input_command)
	test_flag = decrypt(res, privkey = privkey)
	assert test_flag == flag
