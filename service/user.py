import glob
import json
import os

USER_DIR = './private/'
USER_EXT = '.data'

def load(username):
    fname = USER_DIR + username + USER_EXT
    if os.path.isfile(fname):
        with open(fname, 'r') as f:
            return json.load(f)
    else:
        return {}

def save(username, data):
    fname = USER_DIR + username + USER_EXT
    with open(fname, 'w') as f:
        json.dump(data, f)

def list_users():
    user_files = glob.glob(USER_DIR + '*' + USER_EXT)
    users = [os.path.splitext(os.path.basename(f))[0] for f in user_files]
    print('list_users', users)
    return users

class User():
    def __init__(self, username):
        self.username = username
        self._data = load(username)

    def set(self, key, val):
        self._data[key] = val
        save(self.username, self._data)
    def get(self, key):
        return self._data.get(key)
