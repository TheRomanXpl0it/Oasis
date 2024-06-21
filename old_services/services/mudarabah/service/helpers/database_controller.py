import psycopg2
from hashlib import md5

from models.user_model import User

conn = None

def connect_to_db():
    global conn
    conn = psycopg2.connect(dbname='postgres', user='postgres', password='postgres', host='postgres')

def check_and_refresh_connect():
    global conn
    try:
        conn.isolation_level
    except psycopg2.OperationalError:
        connect_to_db()

class DatabaseClient:
    def __init__(self):
        pass

    def __enter__(self):
        check_and_refresh_connect()
        global conn
        self.conn = conn  
        self.cursor = conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cursor.close()

    def check_if_username_free(self, username):
        self.cursor.execute('SELECT * FROM public.users WHERE login = %s', (username, ))
        u = self.cursor.fetchone()
        return u is None

    def add_user(self, user):
        self.cursor.execute("INSERT INTO public.users (login, password_hash, private_key, credit_card_credentials, balance, cookie) VALUES(%s, %s, %s, %s, %s, %s)", (user.login, user.password_hash, psycopg2.Binary(user.private_key), user.credit_card_credentials, user.balance, user.cookie))

    def get_all_users(self):
        self.cursor.execute('SELECT login FROM public.users')
        return [x[0] for x in self.cursor.fetchall()]

    def get_user_by_login_and_pass(self, username, password):
        password_hash = md5(password.encode('utf-8')).hexdigest()
        self.cursor.execute('SELECT * FROM public.users WHERE login=%s AND password_hash=%s', (username, password_hash))
        u = self.cursor.fetchone()
        return User.load(u) if u else None

    def get_user_by_login(self, username):
        username = str(username)
        self.cursor.execute('SELECT * FROM public.users WHERE login=%s', (username, ))
        u = self.cursor.fetchone()
        return User.load(u) if u else None

    def get_user_by_cookie(self, cookie):
        self.cursor.execute('SELECT * FROM public.users WHERE cookie=%s', (cookie, ))
        u = self.cursor.fetchone()
        return User.load(u) if u else None

    def check_credit_card(self, login, credit_card):
        self.cursor.execute('SELECT * FROM public.users WHERE login=%s AND credit_card_credentials LIKE %s', (login, credit_card))
        u = self.cursor.fetchone()
        return User.load(u) if u else None

    def get_users_transactions(self, login):
        self.cursor.execute('SELECT * FROM transactions WHERE login_to=%s', (login,))
        return self.cursor.fetchall()

    def add_transaction(self, transaction):
        self.cursor.execute("INSERT INTO public.transactions (login_from, login_to, amount, description) VALUES(%s, %s, %s, %s)", (transaction.login_from, transaction.login_to, transaction.amount, psycopg2.Binary(transaction.description)))

    def update_balance(self, login, new_balance):
        self.cursor.execute('UPDATE users SET balance=%s WHERE login=%s', (new_balance, login))
