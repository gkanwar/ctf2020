import base64
import json
import os
import random
import string
import time
from Crypto import Random
from Crypto.Cipher import AES
from user import User
from util import get_utc_past, get_utc_future
from aes import pad, unpad

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


SESSION_EXPIRE_SECONDS = 10*60
session_last_access = {}
def clear_old_sessions():
    global session_last_access
    updated = {}
    for k in session_last_access:
        last_access = session_last_access[k]
        if time.time() - last_access > SESSION_EXPIRE_SECONDS:
            del os.environ[k]
        else:
            updated[k] = last_access
    session_last_access = updated

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
        self.privileged = False
        if self.sid is not None:
            self.load_store(user_check, handshake)

    def load_store(self, user_check, handshake):
        assert self.sid is not None
        if not self.sid in os.environ:
            self.sid = None
            return
        session_last_access[self.sid] = time.time()
        clear_old_sessions()
        store_crypt = base64.b64decode(os.environ[self.sid].encode('utf-8'))
        iv = store_crypt[:AES.block_size]
        cipher = AES.new(STORE_KEY, AES.MODE_CBC, iv)
        store_json = unpad(cipher.decrypt(store_crypt[AES.block_size:]))
        store = json.loads(store_json.decode('utf-8'))
        if store['username'] != user_check:
            self.sid = None
            return
        if handshake is not None and store.get('handshake') == handshake:
            self.privileged = True
        self._store = store
        self.user = User(store['username'])

    def save_store(self):
        assert self.sid is not None
        session_last_access[self.sid] = time.time()
        clear_old_sessions()
        store_pad = pad(json.dumps(self._store).encode('utf-8'))
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
            self.privileged = True
        self.save_store()

    def get(self, key):
        return self._store.get(key) or self.user.get(key)
    def set(self, key, val):
        if not self.privileged: return False
        self._store[key] = val
        self.save_store()
        return True
    def set_persist(self, key, val):
        if not self.privileged: return False
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
        expiry = f'Expires={get_utc_future(SESSION_EXPIRE_SECONDS)}'
        cookies = [
            f'{SESS_COOKIE_NAME}={self.sid}; {expiry}',
            f'{USER_COOKIE_NAME}={username}; {expiry}'
        ]
        if self.privileged:
            handshake = self._store['handshake']
            cookies.append(f'{HANDSHAKE_COOKIE_NAME}={handshake}; {expiry}')
        return cookies

    def __bool__(self):
        return self.sid is not None
