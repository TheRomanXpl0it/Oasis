from utils import *
import os
from rich.prompt import Prompt
import json


def register_user(console, user=None):
    try:
        username = Prompt.ask("username")
        password = Prompt.ask("password")

        if not validate_string(username) or not validate_string(password):
            console.print("Invalid username or password")
            return None

        os.makedirs(os.path.join(user_path, username))

        with open(os.path.join(user_path, username, "password"), "x") as f:
            f.write(password)

        with open(os.path.join(user_path, username, "authorized_polls"), "x") as f:
            f.write(json.dumps([]))

        console.print("User registered correctly!")
        return username
    except FileExistsError:
        console.print("User already registered!")
        return None
    except:
        console.print_exception(show_locals=True)
        return None


def login(console, user=None):
    try:
        username = Prompt.ask("username")

        if not os.path.isfile(os.path.join(user_path, username, "password")):
            console.print("User does not exist")
            return None

        with open(os.path.join(user_path, username, "password"), "r") as f:
            loaded_password = f.read().strip()

        password = Prompt.ask("password")

        if password != loaded_password:
            console.print("Wrong password")
            return None

        console.print("Successfully logged in!")
        return username
    except:
        console.print_exception(show_locals=True)
        return None


def logout(console, user=None):
    return None
