import json
import urllib.request
from base64 import b85decode
from arg_parse import get_parsed_args
from cipher.crypter import Crypter

HOST = "http://{}:3113"


def send_money(host, cookie, login_to, amount, description, priv_key):
    crypter = Crypter.load_private(priv_key)
    new_conditions = {"addition": {"cookie":cookie, "login_to":login_to, "amount":int(amount), "description":crypter.encrypt(description.encode()).hex()}}
    req = urllib.request.Request(host+"/send_money",
                                    data=json.dumps(new_conditions).encode('utf-8'),
                                    headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))


def get_cookie(host, login, password):
    new_conditions = {"addition": {"login": login, "password":password}}
    req = urllib.request.Request(host+"/get_cookie", data=json.dumps(new_conditions).encode('utf-8'),
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))["addition"]["cookie"]


def check_card(host, login, credit_card_credentials):
    new_conditions = {"addition": {"login": login, "credit_card_credentials": credit_card_credentials}}
    req = urllib.request.Request(host+"/check_card", data=json.dumps(new_conditions).encode('utf-8'),
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))["addition"]


def register(host, login, password, credit_card_credentials):
    new_conditions = {"addition": {"login": login, "password":password, "credit_card_credentials":credit_card_credentials}}
    req = urllib.request.Request(host+"/register", data=json.dumps(new_conditions).encode('utf-8'),
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))["addition"]


def get_transaction(host, login):
    new_conditions = {"addition": {"login": login}}
    req = urllib.request.Request(host+"/transactions", data=json.dumps(new_conditions).encode('utf-8'),
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))["addition"]


def get_user(host, login):
    new_conditions = {"addition": {"login": login}}
    req = urllib.request.Request(host+"/get_user", data=json.dumps(new_conditions).encode('utf-8'),
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))["addition"]


def get_user_listing(host):
    req = urllib.request.Request(host+"/list_users",
                                 headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf8'))["addition"]


def main():
    args = get_parsed_args()
    host = HOST.format(args.host)
    if args.register:
        res = register(host, args.login, args.password, args.credit_card_credentials)
        priv_key = res["priv_key"]
        with open(f"{args.login}.key", "wb") as f:
            f.write(b85decode(priv_key.encode()))
            print(f"key is written to {args.login}.key")
        print(res)
    if args.get_cookie:
        print(get_cookie(host, args.login, args.password))
    if args.send_money:
        if args.priv_key_filename:
            with open(args.priv_key_filename, "rb") as f:
                key = f.read()
        else:
            key = args.priv_key 
        print(send_money(host, args.cookie, args.login_to, args.amount, args.description, key))
    if args.get_transactions:
        print(get_transaction(host, args.login))
    if args.get_user:
        print(get_user(host, args.login))
    if args.get_user_listing:
        print(get_user_listing(host))
    if args.check_card:
        print(check_card(host, args.login, args.credit_card_credentials))

if __name__ == "__main__":
    main()