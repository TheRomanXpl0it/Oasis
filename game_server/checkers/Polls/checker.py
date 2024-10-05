#!/usr/bin/env python3

from pwn import *
import checklib
import random
import string
import sys
import os
import json
import re
os.environ["PWNLIB_NOTERM"] = "1"

context.timeout = 5
context.log_level = "error"

data = checklib.get_data()
action = data['action']
team_addr = data['host']
port = 5000

def get_random_string(n, alph=string.ascii_letters+string.digits):
    return ''.join([random.choice(alph) for _ in range(n)])

def check_sla():
    try:
        r = remote(team_addr, port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot connect", str(e))

    user = get_random_string(random.randint(10, 16))
    password = get_random_string(random.randint(10, 16))
    description = get_random_string(random.randint(10, 20))
    n_options = random.randint(3, 7)
    options = [get_random_string(random.randint(5, 10))
               for _ in range(n_options)]
    try:
        r.recvuntil(b": ")
        r.sendline(b"register")
        r.recvuntil(b": ")
        r.sendline(user.encode())
        r.recvuntil(b": ")
        r.sendline(password.encode())
        assert b"User registered correctly!" in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot register", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"create poll")
        r.recvuntil(b": ")
        r.sendline(description.encode())
        r.recvuntil(b": ")
        r.sendline(str(n_options).encode())
        for i in range(n_options):
            r.recvuntil(b": ")
            r.sendline(options[i].encode())
        resp = r.recvline()
        poll_id = resp.split()[-1].decode()
        assert b"Poll created!" in resp
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot create poll", str(e))

    r.close()

    try:
        r = remote(team_addr, port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot connect", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"login")
        r.recvuntil(b": ")
        r.sendline(user.encode())
        r.recvuntil(b": ")
        r.sendline(password.encode())
        assert b"Successfully logged in!" in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot login", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"access poll")
        resp = r.recvuntil(b": ")
        poll_id = re.findall(b"[0-9a-f]{16}", resp)[0]
        r.sendline(b"show")
        r.recvuntil(b": ")
        r.sendline(poll_id)
        assert description.encode() in r.recvuntil(
            b": ").replace(b" ", b"").replace(b"\n", b"")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot access poll", str(e))

    r.close()

    try:
        r = remote(team_addr, port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot connect", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"login")
        r.recvuntil(b": ")
        r.sendline(user.encode())
        r.recvuntil(b": ")
        r.sendline(password.encode())
        assert b"Successfully logged in!" in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot login", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"access poll")
        resp = r.recvuntil(b": ")
        poll_id = re.findall(b"[0-9a-f]{16}", resp)[0]
        r.sendline(b"share")
        r.recvuntil(b": ")
        r.sendline(poll_id)
        token = r.recvline().split()[-1].decode()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot share poll", str(e))

    r.close()

    user = get_random_string(random.randint(10, 16))
    password = get_random_string(random.randint(10, 16))

    try:
        r = remote(team_addr, port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot connect", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"register")
        r.recvuntil(b": ")
        r.sendline(user.encode())
        r.recvuntil(b": ")
        r.sendline(password.encode())
        assert b"User registered correctly!" in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot register", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"use token")
        resp = r.recvuntil(b": ")
        r.sendline(token.encode())
        assert b"OK" in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot use sharing token", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"access poll")
        resp = r.recvuntil(b": ")
        poll_id = re.findall(b"[0-9a-f]{16}", resp)[0]
        r.sendline(b"show")
        r.recvuntil(b": ")
        r.sendline(poll_id)
        assert description.encode() in r.recvuntil(
            b": ").replace(b" ", b"").replace(b"\n", b"")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot access poll", str(e))

    checklib.quit(checklib.Status.OK)


def put_flag():
    flag = data['flag']
    random.seed(flag)

    try:
        r = remote(team_addr, port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot connect", str(e))

    user = get_random_string(random.randint(10, 16))
    password = get_random_string(random.randint(10, 16))
    n_options = random.randint(3, 7)
    options = [get_random_string(random.randint(5, 10))
               for _ in range(n_options)]
    try:
        r.recvuntil(b": ")
        r.sendline(b"register")
        r.recvuntil(b": ")
        r.sendline(user.encode())
        r.recvuntil(b": ")
        r.sendline(password.encode())
        assert b"User registered correctly!" in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot register", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"create poll")
        r.recvuntil(b": ")
        r.sendline(flag.encode())
        r.recvuntil(b": ")
        r.sendline(str(n_options).encode())
        for i in range(n_options):
            r.recvuntil(b": ")
            r.sendline(options[i].encode())
        resp = r.recvline()
        poll_id = resp.split()[-1].decode()
        assert b"Poll created!" in resp
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot create poll", str(e))

    try:
        checklib.post_flag_id({"poll_id": poll_id, "username": user})
    except Exception as e:
        checklib.quit(checklib.Status.ERROR, "Checker error", str(e))
    
    checklib.quit(checklib.Status.OK)


def get_flag():
    flag = data['flag']
    random.seed(flag)

    try:
        r = remote(team_addr, port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot connect", str(e))

    user = get_random_string(random.randint(10, 16))
    password = get_random_string(random.randint(10, 16))

    try:
        r.recvuntil(b": ")
        r.sendline(b"login")
        r.recvuntil(b": ")
        r.sendline(user.encode())
        r.recvuntil(b": ")
        r.sendline(password.encode())
        assert b"Successfully logged in!" in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot login", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(b"access poll")
        resp = r.recvuntil(b": ")
        poll_id = re.findall(b"[0-9a-f]{16}", resp)[0]
        r.sendline(b"show")
        r.recvuntil(b": ")
        r.sendline(poll_id)
        assert flag.encode() in r.recvuntil(b": ").replace(b" ", b"").replace(b"\n", b"")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot access poll", str(e))

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
