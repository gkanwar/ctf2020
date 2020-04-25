import bcrypt
import os
import re

AUTH_DIR = './private/'
AUTH_SALT_ROUNDS = 6
AUTH_USER_REGEX = r'^[a-zA-Z0-9]{4,32}$'

def check_login(username, password):
    if not re.match(AUTH_USER_REGEX, username):
        return False, 'Invalid username'
    if not os.path.isfile(AUTH_DIR + username):
        return False, 'Account does not exist'
    with open(AUTH_DIR + username, 'rb') as f:
        true_pass_hash = f.read()
    if not bcrypt.checkpw(password.encode('utf-8'), true_pass_hash):
        return False, 'Wrong password'
    return True, 'Success'

def register_user(username, password):
    if not re.match(AUTH_USER_REGEX, username):
        return False, 'Invalid username'
    if os.path.isfile(AUTH_DIR + username):
        return False, 'Account already exists'
    salt = bcrypt.gensalt(AUTH_SALT_ROUNDS)
    pass_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    with open(AUTH_DIR + username, 'wb') as f:
        f.write(pass_hash)
    return True, 'Success'
