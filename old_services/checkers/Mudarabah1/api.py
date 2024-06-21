import requests

PORT = 3113
HEADERS = {'content-type': 'application/json'}

class Api:
    def __init__(self, host):
        self.hostname = f"http://{host}:{PORT}"

    def ping(self):
        try:
            r = requests.get(f"{self.hostname}/ping")
            return r.json()
        except Exception:
            return None

    def register(self, login, password, credit_card_credentials):
        data = {"addition": {
            "login": login, 
            "password": password, 
            "credit_card_credentials": credit_card_credentials
        }}
        try:
            r = requests.post(f"{self.hostname}/register", json=data, headers=HEADERS)
            return r.json()
        except Exception:
            return None

    def send_money(self, cookie, login_to, amount, description):
        data = {"addition": {
            "cookie": cookie,
            "login_to": login_to,
            "amount": amount,
            "description": description
        }}
        try:
            r = requests.post(f"{self.hostname}/send_money", json=data, headers=HEADERS)
            return r.json()
        except Exception:
            return None

    def get_cookie(self, login, password):
        data = {"addition": {
            "login": login,
            "password": password
        }}
        try:
            r = requests.post(f"{self.hostname}/get_cookie", json=data, headers=HEADERS)
            return r.json()
        except Exception:
            return None

    def get_user(self, login):
        data = {"addition": {
            "login": login,
        }}
        try:
            r = requests.post(f"{self.hostname}/get_user", json=data, headers=HEADERS)
            return r.json()
        except Exception:
            return None

    def get_transacions(self, login):
        data = {"addition": {
            "login": login,
        }}
        try:
            r = requests.post(f"{self.hostname}/transactions", json=data, headers=HEADERS)
            return r.json()
        except Exception:
            return None
    
    def list_users(self):
        try:
            r = requests.get(f"{self.hostname}/list_users")
            return r.json()
        except Exception:
            return None

    def check_card(self, login, credit_card_credentials):
        data = {"addition": {
            "login": login,
            "credit_card_credentials": credit_card_credentials
        }}
        try:
            r = requests.post(f"{self.hostname}/check_card", json=data, headers=HEADERS)
            return r.json()
        except Exception:
            return None