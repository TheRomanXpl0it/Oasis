import json
from base64 import b85encode
from flask import Flask, request, redirect, url_for, render_template, session, jsonify

from cipher.code import LDPC
from cipher.crypter import Crypter
from helpers.database_controller import DatabaseClient, connect_to_db
from helpers.decorators import need_args
from models.user_model import User
from models.transaction_model import Transaction

app = Flask(__name__)
app.secret_key = "secret_key"


@app.before_first_request
def before_request():
    connect_to_db()


@app.route('/send_money', methods=['POST'])
@need_args("cookie", "login_to", "amount", "description")
def send_money(cookie=None, login_to=None, description=None, amount=None):
    with DatabaseClient() as db:
        user_from = db.get_user_by_cookie(cookie)
        if not user_from:
            return jsonify({"status": 400, "addition": {"error": "No user with this cookie"}})
        user_to = db.get_user_by_login(login_to)
        if not user_to:
            return jsonify({"status": 400, "addition": {"error": "No user with login_to"}})
        if user_from.balance < amount or amount < 0:
            return jsonify({"status": 400, "addition": {"error": "Not enough money to make transaction"}})
    crypter = Crypter.load_private(user_from.private_key)
    description = crypter.decrypt(bytes.fromhex(description))
    transaction = Transaction(user_from.login, user_to.login, amount, description)
    with DatabaseClient() as db:
        db.update_balance(user_from.login, user_from.balance - transaction.amount)
        db.update_balance(user_to.login, user_to.balance + transaction.amount)
        db.add_transaction(transaction)

    return jsonify({"status": 200})


@app.route('/get_cookie', methods=['POST'])
@need_args("login", "password")
def login(login=None, password=None):
    with DatabaseClient() as db:
        user = db.get_user_by_login_and_pass(login, password)
    if not user:
        return jsonify({"status": 400, "addition": {"error": "Incorrect username or password"}})
    return jsonify({"status": 200, "addition": {"cookie": user.cookie}})


@app.route('/check_card', methods=['POST'])
@need_args("login", "credit_card_credentials")
def check_card(login=None, credit_card_credentials=None):
    with DatabaseClient() as db:
        user = db.check_credit_card(login, credit_card_credentials)
    if not user:
        return jsonify({"status": 400, "addition": {"error": "Wrong login or credit card"}})
    return jsonify({"status": 200, "addition": {"credit_card_credentials": user.credit_card_credentials}})


@app.route('/register', methods=['POST'])
@need_args("login", "password", "credit_card_credentials")
def register(login=None, password=None, credit_card_credentials=None):
    with DatabaseClient() as db:
        if not db.check_if_username_free(login):
            return jsonify({"status": 400, "addition": {"error": "There exists user with this login"}})
    try:
        code = LDPC.from_params(512, 4, 8)
        crypter = Crypter.from_code(code)
        private_key = crypter.dump_private()
        user = User.create(login, password, private_key, credit_card_credentials)
    except Exception:
        return jsonify({"status": 500, "addition": {"error": "Can not create user"}})
    with DatabaseClient() as db:
        db.add_user(user)
    return jsonify({"status": 200, "addition": {"cookie":user.cookie, "priv_key":b85encode(private_key).decode()}})


@app.route('/transactions', methods=["POST"])
@need_args("login")
def get_transactions(login=None):
    with DatabaseClient() as db:
        user = db.get_user_by_login(login)
        if not user:
            return jsonify({"status": 400, "addition": {"error": "Wrong login"}})
        transactions = db.get_users_transactions(login)
        if not transactions:
            return jsonify({"status": 400, "addition": {"error": "User has no transactions"}})

    crypter = Crypter.load_private(user.private_key)
    transactions = list(map(Transaction.load, transactions))
    transactions = [{
        "login_from": x.login_from,
        "login_to": x.login_to,
        "amount": x.amount,
        "description": crypter.encrypt(x.description).hex()
    } for x in transactions]
    return jsonify({"status": 200, "addition": {"transactions": transactions}})


@app.route('/get_user', methods=["POST"])
@need_args("login")
def get_user(login=None):
    with DatabaseClient() as db:
        user = db.get_user_by_login(login)
        if user is None:
            return jsonify({"status": 400, "addition": {"error": "No user with this login"}})
    crypter = Crypter.load_private(user.private_key)
    pub_key = b85encode(crypter.dump_public()).decode()
    return jsonify({"status": 200, "addition": {"login": user.login, "balance": user.balance, "pub_key": pub_key}})


@app.route('/list_users')
def list_users():
    with DatabaseClient() as db:
        users = db.get_all_users()
    return jsonify({"status": 200, "addition": {"users": users}})


@app.route("/ping")
def ping():
    return jsonify({"status": 200})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3113, debug=True)