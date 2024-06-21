#!/usr/bin/env python3

import sys
import os
from binascii import unhexlify, hexlify
import string
from Crypto.PublicKey import RSA
from hashlib import sha256

import asyncio
import aiosqlite

from crypto import decrypt, encrypt, sign, verify


if os.path.isfile('key.pem'):
    try:
        KEY = RSA.importKey(open('key.pem','r').read())
    except:
        KEY = RSA.generate(2048)
        key_file = open('key.pem','wb')
        key_file.write(KEY.export_key())
        key_file.close()
else:
    KEY = RSA.generate(2048)
    key_file = open('key.pem','wb')
    key_file.write(KEY.export_key())
    key_file.close()

PUBLIC_KEY = KEY.public_key().export_key()

if os.path.isfile('checker.pubkey'):
    CHECKER_KEY = RSA.importKey(open('checker.pubkey','r').read())
else:
    raise Exception('Public Key of Checker not found')

global DB_CONN

class Store(object):
    def __init__(self, rx, tx):
        self.rx = rx
        self.tx = tx
    
    async def run(self):
        self.tx.write(b"Send command to execute, format: `<load|store|send_pubkey> <args> ...`\n")
        await self.tx.drain()
        while True:
            try:
                self.tx.write(b"command: ")
                await self.tx.drain()

                line = await self.rx.readline()
                # print(f"Received command: {line}")

                input_data = line.strip()
                if not input_data:
                    break
                
                await self.process_command(input_data)
                await self.tx.drain()

            except EOFError:
                break
            except (UnicodeError, IndexError) as e:
                print(e, file=sys.stderr)
                break
            

    async def process_command(self, input_data : bytes) -> str:
        args = input_data.decode().split(' ') # split signature
        command = args[0]

        if command == 'store':
            #checking signature
            if len(args) != 5:
                self.tx.write(b"Entered line must have format \"store category data tick signature\"\n")
                return

            signature = args[-1]
            args = args[1:-1]
            if not verify(' '.join(args), signature, CHECKER_KEY):
                self.tx.write(b"invalid signature\n")
                return

            await self.handle_store(*args)

        elif command == 'load':
            try:
                tick = int(args[1])
            except ValueError:
                self.tx.write(b'First argument must be integer\n')
            await self.handle_load(args[1])

        elif command == 'send_pubkey':
            self.tx.write(PUBLIC_KEY + b'\n')
        else:
            self.tx.write(b'Unknown command\n')
            #print("Entered line must have format \"command [params]* [signature]\" separated by spaces")

    async def handle_store(self, category : str, data : str, tick : str) -> str:
        if category == 'flag':
            data = decrypt(data, privkey = KEY)
        else:
            data = unhexlify(data).decode()
        #store data in DB
        try:
            tick = int(tick)
        except ValueError:
            self.tx.write(b'tick must be integer\n')
            return

        if all([char in string.printable for char in data]):
            async with DB_CONN.execute('insert into store (tick, category, data) values (?,?,?);', (tick, category, data)) as cursor:
                last_id = cursor.lastrowid
            
            if last_id is None:
                self.tx.write(b'Failed to add element to db.\n')
                return 

            await DB_CONN.commit()
            self.tx.write(f"{sha256(data.encode()).hexdigest()}:{last_id}\n".encode())
        else:
            self.tx.write(f'Data not correctly decrypted: {data.encode()}\n'.encode())

    async def handle_load(self, flag_id : int) -> str:
        async with DB_CONN.execute('select data,category from store where id = ' + str(flag_id) + ';') as cursor:
            try:
                content, category = await cursor.fetchone() 
            except TypeError:
                self.tx.write(b'Key not in Database\n')
                return

        # print(content, category, file=sys.stderr)
        if category == 'flag':
            self.tx.write(f"{encrypt(content, CHECKER_KEY)}\n".encode())
        else:
            self.tx.write(hexlify(content.encode()) + b'\n')

async def handle_connection(reader, writer):
    s = Store(reader, writer)
    await s.run()
    writer.close()
    await writer.wait_closed()

async def main():
    global DB_CONN
    DB_CONN = await aiosqlite.connect('data/store.db')

    server = await asyncio.start_server(handle_connection, host="0.0.0.0", port="9122")
    
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())