#!/usr/bin/env python3

import sys
from rich.console import Console
from rich.prompt import Prompt
from user_handlers import *
from poll_handlers import *
from utils import *

banner = " ---- Polls ---- "

menu_no_login = (["register", "login", "exit"], [
                 register_user, login, exit_service])
menu_login = (["create poll", "access poll", "use token", "logout", "exit"], [
              create_poll, access_poll, validate_token, logout, exit_service])


def main():
    user = None
    console = Console(width=100)
    console.print(banner)

    while True:
        try:
            if user is None:
                options = menu_no_login
            else:
                options = menu_login
            cmd = Prompt.ask("What do you want to do?", choices=options[0])
            user = options[1][options[0].index(cmd)](console, user)
        except Exception as e:
            console.print_exception(show_locals=True)


if __name__ == '__main__':
    main()
