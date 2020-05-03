import bcrypt
import os
import re
from user import init_user

AUTH_DIR = './files_private/'
AUTH_SALT_ROUNDS = 6
AUTH_USER_REGEX = r'^[a-zA-Z0-9]{4,32}$'

def check_username(username):
    return bool(re.match(AUTH_USER_REGEX, username))
def check_user_exists(username):
    return check_username(username) and os.path.isfile(AUTH_DIR + username)

def check_login(username, password):
    if not check_username(username):
        return False, 'Invalid username'
    if not os.path.isfile(AUTH_DIR + username):
        return False, 'Account does not exist'
    with open(AUTH_DIR + username, 'rb') as f:
        true_pass_hash = f.read()
    if not bcrypt.checkpw(password.encode('utf-8'), true_pass_hash):
        return False, 'Wrong password'
    return True, 'Success'

def register_user(username, password):
    if not check_username(username):
        return False, 'Invalid username'
    if os.path.isfile(AUTH_DIR + username):
        return False, 'Account already exists'
    salt = bcrypt.gensalt(AUTH_SALT_ROUNDS)
    pass_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    with open(AUTH_DIR + username, 'wb') as f:
        f.write(pass_hash)
    try:
        init_user(username)
    except Exception as e:
        os.remove(AUTH_DIR + username)
        raise
    return True, 'Success'
