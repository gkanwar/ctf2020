import base64
import json
import os
import random
import string
from Crypto import Random
from Crypto.Cipher import AES
from user import User
from util import get_utc_past

SESS_COOKIE_NAME = 'session_id'
USER_COOKIE_NAME = 'username'
HANDSHAKE_COOKIE_NAME = 'session_handshake'
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
            return Session(cookies[SESS_COOKIE_NAME], cookies[USER_COOKIE_NAME],
                           cookies.get(HANDSHAKE_COOKIE_NAME))

    def __init__(self, session_id=None, user_check=None, handshake=None):
        self.sid = session_id
        self.writeable = False
        if self.sid is not None:
            self.load_store(user_check, handshake)

    def load_store(self, user_check, handshake):
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
        if handshake is not None and store.get('handshake') == handshake:
            self.writeable = True
        self._store = store
        self.user = User(store['username'])

    def save_store(self):
        assert self.sid is not None
        store_pad = pad(json.dumps(self._store))
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(STORE_KEY, AES.MODE_CBC, iv)
        os.environ[self.sid] = base64.b64encode(iv + cipher.encrypt(store_pad)).decode('utf-8')

    def setup(self):
        self._store = {}
        self.sid = 'SID' + ''.join(random.choices(string.ascii_letters, k=SESSION_ID_LEN))
        self.save_store()

    def activate_login(self, username, handshake):
        if not self: self.setup()
        self._store['username'] = username
        self.user = User(username)
        if handshake is not None:
            self._store['handshake'] = handshake
            self.writeable = True
        self.save_store()

    def get(self, key):
        return self._store.get(key) or self.user.get(key)
    def set(self, key, val):
        if not self.writeable: return False
        self._store[key] = val
        self.save_store()
        return True
    def set_persist(self, key, val):
        if not self.writeable: return False
        self.user.set(key, val)
        return True

    def get_cookies(self):
        if not self: # clear cookies if no valid session
            return [
                f'{SESS_COOKIE_NAME}=; Expires={get_utc_past()}',
                f'{USER_COOKIE_NAME}=; Expires={get_utc_past()}',
                f'{HANDSHAKE_COOKIE_NAME}=; Expires={get_utc_past()}'
            ]
        username = self._store['username']
        cookies = [
            f'{SESS_COOKIE_NAME}={self.sid}',
            f'{USER_COOKIE_NAME}={username}'
        ]
        if self.writeable:
            handshake = self._store['handshake']
            cookies.append(f'{HANDSHAKE_COOKIE_NAME}={handshake}')
        return cookies

    def __bool__(self):
        return self.sid is not None
