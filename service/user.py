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

class User():
    def __init__(self, username):
        self.username = username
        self._data = load(username)

    def set(self, key, val):
        self._data[key] = val
        save(self.username, self._data)
    def get(self, key):
        return self._data.get(key)
