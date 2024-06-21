#!/usr/bin/env python3

import random
from base64 import b85decode
from string import ascii_letters, digits

from cipher.crypter import Crypter
from api import Api

import hashlib
import os
import random
import string

import requests
import bs4

import checklib

os.makedirs('flag_ids', exist_ok=True)


data = checklib.get_data()
action = data['action']
team_id = data['teamId']
service_addr = '10.60.' + team_id + '.1'
service_name = 'mudarabah'
if 'flag' in data:
    flag = data['flag']

ALPHA = ascii_letters + digits


def check_sla():
    api = Api(service_addr)
    res, err = ping(api)
    if err: return err

    res, err = register(api)
    if err: return err

    login, password, card, priv_key, cookie = res

    try:
        if len(b85decode(priv_key.encode())) > 23000:
            return checklib.quit(checklib.Status.DOWN, "Private key is too big")
    except Exception:
        return checklib.quit(checklib.Status.DOWN, "Wrong private key format")

    res, err = get_cookie(api, login, password)
    if err: return err
    if res != cookie:
        return checklib.quit(checklib.Status.DOWN, "Wrong cookie")

    users, err = list_users(api)
    if err: return err
    if login not in users:
        return checklib.quit(checklib.Status.DOWN, "User not in users")

    res, err = check_card(api, login, card)
    if err: return err
    if res != card:
        return checklib.quit(checklib.Status.DOWN, "Wrong credit card")

    return checklib.quit(checklib.Status.OK)

# VULN 1
def put_1():
    api = Api(service_addr)

    res, err = register(api)
    if err: return err
    login1, password1, card1, priv_key1, cookie1 = res

    try:
        if len(b85decode(priv_key1.encode())) > 23000:
            return checklib.quit(checklib.Status.DOWN, "Private key is too big")
    except Exception:
        return checklib.quit(checklib.Status.DOWN, "Wrong private key format")


    res, err = register(api)
    if err: return err
    login2, password2, card2, priv_key2, cookie2 = res

    try:
        if len(b85decode(priv_key2.encode())) > 23000:
            return checklib.quit(checklib.Status.DOWN, "Private key is too big")
    except Exception:
        return checklib.quit(checklib.Status.DOWN, "Wrong private key format")


    try:
        crypter = Crypter.load_private(b85decode(priv_key2.encode()))
    except Exception as ex:
        return checklib.quit(checklib.Status.DOWN, "Can't load private key")

    amount = random.randint(1, 100)
    description = crypter.encrypt(flag.encode())

    res, err = send_money(api, cookie2, login1, amount, description.hex())
    if err: return err

    users, err = list_users(api)
    if err: return err
    if login1 not in users or login2 not in users:
        return checklib.quit(checklib.Status.DOWN, "No user in users")

    flag_id = f'{login1}:{password1}:{priv_key1}:{cookie1}'

    with open(f'flag_ids/{flag}', 'w') as f:
        f.write(flag_id)

    return checklib.quit(checklib.Status.OK)

def get_1():
    try:
        with open(f'flag_ids/{flag}', 'r') as f:
            flag_id = f.read()
    except FileNotFoundError:
        return checklib.quit(checklib.Status.DOWN, "No flag id")
    
    login, password, priv_key, cookie = flag_id.strip().split(':')
    api = Api(service_addr)

    res, err = get_cookie(api, login, password)
    if err: return err
    if res != cookie:
        return checklib.quit(checklib.Status.DOWN, "Wrong cookie")

    try:
        crypter = Crypter.load_private(b85decode(priv_key.encode()))
    except Exception as ex:
        print(ex)
        return checklib.quit(checklib.Status.DOWN, "Can't load private key")

    res, err = get_user(api, login)
    if err: return err
    _login, _balance, _pub_key = res

    if b85decode(_pub_key) != crypter.dump_public():
        return checklib.quit(checklib.Status.DOWN, "Wronf public key")

    transactions, err = get_transactions(api, login)
    if err: return err
    descriptions = []
    for transaction in transactions:
        description = bytes.fromhex(transaction['description'])
        descriptions.append(crypter.decrypt(description))

    if flag.encode() not in descriptions:
        return checklib.quit(checklib.Status.DOWN, "Wrong transaction's description")

    return checklib.quit(checklib.Status.OK)

# VULN 2
def put_2():
    api = Api(service_addr)

    res, err = register(api, card=flag)
    if err: return err
    login, password, card, _, cookie = res

    res, err = get_user(api, login)
    if err: return err
    _login, _balance, _ = res
    if _login != login or _balance != 100:
        return checklib.quit(checklib.Status.DOWN, "Wrong user")

    flag_id = f'{login}:{password}:{cookie}'
    with open(f'flag_ids/{flag}', 'w') as f:
        f.write(flag_id)

    return checklib.quit(checklib.Status.OK)

def get_2():
    try:
        with open(f'flag_ids/{flag}', 'r') as f:
            flag_id = f.read()
    except FileNotFoundError:
        return checklib.quit(checklib.Status.DOWN, "No flag id")
    login, password, cookie = flag_id.strip().split(':')
    card = flag
    api = Api(service_addr)

    users, err = list_users(api)
    if err: return err
    if login not in users:
        return checklib.quit(checklib.Status.DOWN, "No user in users")

    res, err = get_cookie(api, login, password)
    if err: return err
    if res != cookie:
        return checklib.quit(checklib.Status.DOWN, "Wrong cookie")
    
    card_pattern = card[:5] + ('_'*(len(card) - 11) + card[-6:])
    res, err = check_card(api, login, card_pattern)
    if err: return err
    if res != card:
        return checklib.quit(checklib.Status.DOWN, "Wrong credit card")

    return checklib.quit(checklib.Status.OK)


def ping(api):
    result = api.ping()
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't ping service")
    if result["status"] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong ping status")
    return "OK", None

def register(api, card=None):
    login = get_random_string(15)
    password = get_random_string(15)
    card = card or get_random_string(32)

    result = api.register(login, password, card)
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't register")

    if result['status'] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong register status")

    if "addition" not in result or "priv_key" not in result["addition"] or "cookie" not in result["addition"]:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong register data")

    priv_key = result["addition"]["priv_key"]
    cookie = result["addition"]["cookie"]

    return (login, password, card, priv_key, cookie), None


def send_money(api, cookie, login_to, amount, description):
    result = api.send_money(cookie, login_to, amount, description)
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't send money")

    if result['status'] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong send money status")

    return 'OK', None

def get_cookie(api, login, password):
    result = api.get_cookie(login, password)
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't get cookie")

    if result['status'] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong cookie status")

    if "addition" not in result or "cookie" not in result["addition"]:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong cookie data")

    cookie = result["addition"]["cookie"]
    return cookie, None

def get_user(api, login):
    result = api.get_user(login)
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't get user")

    if result['status'] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong get user status")

    if "addition" not in result or "pub_key" not in result["addition"] or "login" not in result["addition"] or "balance" not in result["addition"]:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong user data")

    login = result["addition"]["login"]
    balance = result["addition"]["balance"]
    pub_key = result["addition"]["pub_key"]
    return (login, balance, pub_key), None

def get_transactions(api, login):
    result = api.get_transacions(login)
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't get transactions")

    if result['status'] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong get tranaction status")

    if "addition" not in result or "transactions" not in result["addition"]:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong transactions data")

    transactions = result["addition"]["transactions"]
    return transactions, None

def list_users(api):
    result = api.list_users()
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't list users")

    if result['status'] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong list users status")

    if "addition" not in result or "users" not in result["addition"]:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong list users data")

    users = result["addition"]["users"]
    return users, None

def check_card(api, login, credit_card):
    result = api.check_card(login, credit_card)
    if result is None:
        return None, checklib.quit(checklib.Status.DOWN, "Can't check card")

    if result['status'] != 200:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong check card status")

    if "addition" not in result or "credit_card_credentials" not in result["addition"]:
        return None, checklib.quit(checklib.Status.DOWN, "Wrong check card data")

    credit_card_credentials = result["addition"]["credit_card_credentials"]
    return credit_card_credentials, None


def get_random_string(length):
    return ''.join(random.choice(ALPHA) for i in range(length))

def put_flag():
    put_2()

def get_flag():
    get_2()

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