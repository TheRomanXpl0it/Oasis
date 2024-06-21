from utils import *
import os
from rich.prompt import Prompt
from rich.table import Table
import json
from Crypto.Cipher import AES

def create_poll(console, user):
    try:
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        
        poll_dict = {}
        poll_id = os.urandom(8).hex()
        poll_dict["owner"] = user
        poll_dict["description"] = Prompt.ask("Poll description")
        poll_dict["options"] = []
        poll_dict["votes"] = []
        poll_dict["access"] = [[user, 0]]
        poll_n_options = int(Prompt.ask("Number of options"))

        for i in range(1, poll_n_options+1):
            poll_dict["options"].append(Prompt.ask(f"Option {i}"))
            poll_dict["votes"].append(0)

        with open(os.path.join(data_path, poll_id), "x") as f:
            f.write(json.dumps(poll_dict))

        with open(os.path.join(user_path, user, "authorized_polls"), "r") as f:
            my_polls = json.loads(f.read())
        
        my_polls.append(poll_id)

        with open(os.path.join(user_path, user, "authorized_polls"), "w") as f:
            f.write(json.dumps(my_polls))
        
        console.print(f"Poll created! Id: {poll_id}")
        return user
    except:
        console.print_exception(show_locals = True)
        return user

def show_poll(console, poll_id, user):
    with open(os.path.join(data_path, poll_id), "r") as f:
        poll_dict = json.loads(f.read())

    if poll_dict["owner"] != user and user not in sum(poll_dict["access"], []):
        console.print("You don't have access to this poll!")
        return None
    
    table = Table(title = f'{poll_dict["description"]}, by {poll_dict["owner"]}')
    table.add_column("Option")
    table.add_column("Votes")

    for i in range(len(poll_dict["options"])):
        table.add_row(poll_dict["options"][i], str(poll_dict["votes"][i]))

    console.print(table)

    return poll_dict

def vote_poll(console, poll_id, user):
    poll_dict = show_poll(console, poll_id, user)

    if [user, 0] not in poll_dict["access"]:
        console.print("You already voted in this poll or you don't have access to it")
    else:
        option = Prompt.ask("Option to vote")

        if option not in poll_dict["options"]:
            console.print("Option not valid")
        else:
            poll_dict["access"].remove([user, 0])
            poll_dict["access"].append([user, 1])
            poll_dict["votes"][poll_dict["options"].index(option)] += 1
            
            with open(os.path.join(data_path, poll_id), "w") as f:
                f.write(json.dumps(poll_dict))
            
            console.print("Vote registered!")

def share_poll(console, poll_id, user):
    with open(os.path.join(data_path, poll_id), "r") as f:
        poll_dict = json.loads(f.read())
    
    if not poll_dict["owner"]:
        console.print("You are not the owner of the poll!")
    else:
        cipher = AES.new(server_key, AES.MODE_CBC)
        token = cipher.encrypt(poll_id.encode())
        token = cipher.iv + token
        console.print(f"Use this token to share the poll: {token.hex()}")
    


def access_poll(console, user):
    try:
        table = Table(title = "My Polls")
        table.add_column("id")
        table.add_column("owner")
        table.add_column("sharable")

        with open(os.path.join(user_path, user, "authorized_polls"), "r") as f:
            my_polls = json.loads(f.read())
        
        for el in my_polls:
            with open(os.path.join(data_path, el)) as f:
                content = json.loads(f.read())
            table.add_row(el, content["owner"], str(content["owner"] == user))

        console.print(table)

        cmd = Prompt.ask("What do you want to do?", choices = ["show", "vote", "share", "back"], default = "back")

        if cmd != "back":
            poll_id = Prompt.ask("Poll id")

            if not os.path.isfile(os.path.join(data_path, poll_id)):
                console.print("Poll not found")
            else:
                if cmd == "show":
                    show_poll(console, poll_id, user)
                elif cmd == "vote":
                    vote_poll(console, poll_id, user)
                elif cmd == "share":
                    share_poll(console, poll_id, user)
        return user
    except:
        console.print_exception(show_locals = True)
        return user

def validate_token(console, user):
    try:
        token = Prompt.ask("Token")
        ct = bytes.fromhex(token)
        cipher = AES.new(server_key, AES.MODE_CBC, iv = ct[:16])
        poll_id = cipher.decrypt(ct[16:])

        if not os.path.isfile(os.path.join(data_path.encode(), poll_id)):
            console.print("Invalid token")
            return user

        poll_id = poll_id.decode()
        
        with open(os.path.join(user_path, user, "authorized_polls"), "r") as f:
            polls = json.loads(f.read())

        if poll_id not in polls:
            polls.append(poll_id)
        
        with open(os.path.join(user_path, user, "authorized_polls"), "w") as f:
            f.write(json.dumps(polls))

        with open(os.path.join(data_path, poll_id), "r") as f:
            poll_dict = json.loads(f.read())
        
        if [user,0] not in poll_dict["access"]:
            poll_dict["access"].append([user,0])

        with open(os.path.join(data_path, poll_id), "w") as f:
            f.write(json.dumps(poll_dict))

        console.print("Token OK")

        return user
    except:
        console.print_exception(show_locals = True)
        return user

