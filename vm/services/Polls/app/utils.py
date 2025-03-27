import string

user_path = "users"
data_path = "polls"
server_key = b"16_r4ndom_bytes!"


def validate_string(inp, lb=5, ub=64, charset=string.ascii_letters+string.digits):
    if isinstance(inp, str):
        return all([c in charset for c in inp]) and len(inp) >= lb and len(inp) <= ub
    elif isinstance(inp, bytes):
        return all([bytes([c]) in charset.encode() for c in inp]) and len(inp) >= lb and len(inp) <= ub
    return False


def exit_service(*args):
    exit()
