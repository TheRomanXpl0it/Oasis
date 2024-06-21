import json

class Transaction:
    def __init__(self, login_from, login_to, amount, description):
        self.login_from = login_from
        self.login_to = login_to
        self.amount = amount
        self.description = description
    
    def dumps(self):
        data = {
            "login_from": self.login_from, 
            "login_to": self.login_to, 
            "amount": self.amount, 
            "description": self.description
        }
        return json.dumps(data)

    @classmethod
    def load(cls, data):
        _, login_from, login_to, amount, description = data
        return cls(login_from, login_to, amount, description.tobytes())