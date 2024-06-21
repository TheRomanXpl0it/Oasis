from hashlib import md5

from helpers.helpers import create_cookie

class User:
    def __init__(self, login, password, private_key, credit_card_credentials, balance, cookie):
        self.login = login
        self.password_hash = md5(password.encode('utf-8')).hexdigest()
        self.private_key = private_key
        self.credit_card_credentials = credit_card_credentials
        self.balance = balance
        self.cookie = cookie
    
    @classmethod
    def create(cls, login, password, private_key, credit_card_credentials):
        cookie = create_cookie(login, password)
        default_balace = 100
        return cls(login, password, private_key, credit_card_credentials, default_balace, cookie)

    @classmethod
    def load(cls, data):
        _, login, password, private_key, credit_card_credentials, balance, cookie = data
        private_key = private_key.tobytes()
        return cls(login, password, private_key, credit_card_credentials, balance, cookie)