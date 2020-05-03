from Crypto.PublicKey import RSA
import glob
import json
import os

USER_DIR = './files_private/'
USER_EXT = '.data'
RSA_BITS = 1024
RSA_E = 3

def _load(username):
    fname = USER_DIR + username + USER_EXT
    if os.path.isfile(fname):
        with open(fname, 'r') as f:
            return json.load(f)
    else:
        return {}

def _save(username, data):
    fname = USER_DIR + username + USER_EXT
    with open(fname, 'w') as f:
        json.dump(data, f)

def list_users():
    user_files = glob.glob(USER_DIR + '*' + USER_EXT)
    users = [os.path.splitext(os.path.basename(f))[0] for f in user_files]
    return users

def init_user(username):
    rsa_key = RSA.generate(RSA_BITS, e=RSA_E)
    _save(username, {
        'pub_key': {'n': rsa_key.n},
        'priv_key': {'n': rsa_key.n, 'd': rsa_key.d}
    })


class User():
    def __init__(self, username):
        self.username = username
        self._data = _load(username)

    def set(self, key, val):
        self._data[key] = val
        _save(self.username, self._data)
    def get(self, key):
        return self._data.get(key)
