from hashlib import md5


def create_cookie(login, password):
    return md5(f"{login}{password}".encode('utf-8')).hexdigest()