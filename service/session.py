import base64
import json
import os
import random
import string
from Crypto import Random
from Crypto.Cipher import AES

SESS_COOKIE_NAME = 'session_id'
USER_COOKIE_NAME = 'username'
SESSION_ID_LEN = 32
STORE_KEY_FILE = './private/store.key'
if not os.path.isfile(STORE_KEY_FILE):
    STORE_KEY = os.urandom(16)
    with open(STORE_KEY_FILE, 'wb') as f:
        f.write(STORE_KEY)
else:
    with open(STORE_KEY_FILE, 'rb') as f:
        STORE_KEY = f.read(16)

def pad(s):
    padding = AES.block_size - len(s) % AES.block_size
    return s + padding*chr(padding)
def unpad(s):
    padding = s[-1]
    assert isinstance(padding, int)
    return s[:-padding]

class Session():
    @staticmethod
    def from_cookies(cookies):
        if SESS_COOKIE_NAME not in cookies or USER_COOKIE_NAME not in cookies:
            return Session()
        else:
            return Session(cookies[SESS_COOKIE_NAME], cookies[USER_COOKIE_NAME])

    def __init__(self, session_id=None, user_check=None):
        self.sid = session_id
        if self.sid is not None:
            self.load_store(user_check)

    def load_store(self, user_check):
        assert self.sid is not None
        if not self.sid in os.environ:
            self.sid = None
            return
        store_crypt = base64.b64decode(os.environ[self.sid].encode('utf-8'))
        iv = store_crypt[:AES.block_size]
        cipher = AES.new(STORE_KEY, AES.MODE_CBC, iv)
        store_json = unpad(cipher.decrypt(store_crypt[AES.block_size:]))
        store = json.loads(store_json)
        if store['username'] != user_check:
            self.sid = None
            return
        self.store = store

    def save_store(self):
        assert self.sid is not None
        store_pad = pad(json.dumps(self.store))
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(STORE_KEY, AES.MODE_CBC, iv)
        os.environ[self.sid] = base64.b64encode(iv + cipher.encrypt(store_pad)).decode('utf-8')

    def setup(self):
        self.store = {}
        self.sid = 'SID' + ''.join(random.choices(string.ascii_letters, k=SESSION_ID_LEN))
        self.save_store()

    def get_cookie(self):
        username = self.store['username']
        return f'{SESS_COOKIE_NAME}={self.sid}; {USER_COOKIE_NAME}={username}'

    def __bool__(self):
        return self.sid is not None
