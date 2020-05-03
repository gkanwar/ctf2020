from ctf_gameserver.checker import BaseChecker, OK, TIMEOUT, NOTWORKING, NOTFOUND
from Crypto.Cipher import AES
import json
import pickle
import random
import requests
import socket
import string

MONITOR_PORT = 7778

def unpad(s):
    padding = s[-1]
    assert isinstance(padding, int)
    return s[:-padding]

one_word_tokens = ['hello', 'test', 'hihi', 'sup', 'testing', '12341234', 'asdfasdf', '<script>alert("foo")</script>', 'hackhackhack', 'quack', '\' OR TRUE --']
keymash_keys = ['a', 's', 'd', 'f', 'q', 'w', 'e', 'r']
keymash_rarer_keys = ['1', '2', '3', '4', 'f', 'g', 't', '5']
def make_keymash():
    out = ''
    while True:
        u = random.random()
        if u < 0.6:
            out += random.choice(keymash_keys)
        elif u < 0.9:
            out += random.choice(keymash_rarer_keys)
        else:
            return out
def make_sentence():
    u = random.random()
    if u < 0.3: # keymash
        return make_keymash()
    else: # one-word post
        return random.choice(one_word_tokens)

def decrypt_message(message, n_key, d, n, *, logger):
    encrypted = bytes.fromhex(message.get('message', ''))
    iv = encrypted[128*n_key:128*n_key+16]
    encrypted_message = encrypted[128*n_key+16:]
    for i in range(n_key):
        logger.info(f'Attempt {i} to decrypt AES key')
        encrypted_key = encrypted[128*i:128*(i+1)]
        m = int.from_bytes(encrypted_key, byteorder='big')
        aes_key_pad = pow(m, d, n).to_bytes(128, byteorder='big')
        if aes_key_pad[:32] != b'\x00'*32 or aes_key_pad[32:48] != aes_key_pad[48:64]:
            logger.info(f'Failed to decrypt AES key, got {aes_key_pad.hex()}')
            continue
        aes_key = aes_key_pad[32:48]
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        return OK, unpad(cipher.decrypt(encrypted_message))
    logger.error(f'Failed all {n_key} attempts to decrypt')
    return NOTWORKING, None



### Abstract class implementing a few utility methods
class WebChecker(BaseChecker):
    def __init__(self, tick, team, service, ip, *, checker_tag):
        super().__init__(tick, team, service, ip)
        self._prefix = f'http://{ip}'
        self._checker_tag = checker_tag

    def req(self, s, method, path, *, data, timeout, json):
        method = getattr(s, method)
        r = method(self._prefix + path, data=data, timeout=timeout)
        if r.status_code != 200:
            self.logger.error(f'{path} status code {r.status_code}')
            return NOTWORKING, None
        if not json:
            return OK, r
        try:
            j = r.json()
        except ValueError as e:
            self.logger.error('JSON decoding exception', exc_info=True)
            return NOTWORKING, None
        if not 'ok' in j:
            self.logger.error(f'{path} bad JSON response: {j}')
            return NOTWORKING, None
        return OK, j
    def post(self, s, path, *, data, timeout=10, json=True):
        return self.req(s, 'post', path, data=data, timeout=timeout, json=json)
    def get(self, s, path, *, timeout=10, json=True):
        return self.req(s, 'get', path, data=None, timeout=timeout, json=json)

    def make_ident(self, ident_tag, tick, tag=None):
        if tag is not None:
            ident_tag = ident_tag + '_' + tag
        return f'{ident_tag}_{self._checker_tag}_{self._service}_{self._team}_{tick}'
    def get_or_create_user(self, tick, *, tag=None, create=True):
        ident = self.make_ident('creds', tick, tag=tag)
        blob = self.retrieve_blob(ident)
        if blob is not None and blob != b'':
            return OK, pickle.loads(blob)
        self.logger.info(f'Did not find user for tick {tick} with ident {ident}, creating...')
        if not create:
            self.logger.warn(f'User blob does not exist with ident {ident}, probably missed tick')
            return NOTFOUND, None
        username = 'test' + ''.join(random.choices(string.digits , k=16))
        password = ''.join(random.choices(string.printable, k=32))
        creds = {'username': username, 'password': password}
        s = requests.Session()
        status, _ = self.post(s, '/register', data=creds)
        if status != OK: return status, None
        blob = pickle.dumps(creds)
        self.store_blob(ident, blob)
        return OK, creds

    def get_priv_key(self, s):
        status, r = self.get(s, '/priv_key')
        if status != OK: return status, None
        priv_key = r['ok']
        if 'd' not in priv_key or 'n' not in priv_key:
            return NOTWORKING, None
        d, n = int(priv_key['d'], 16), int(priv_key['n'], 16)
        return OK, (d,n)
    def get_pub_key(self, s, username):
        status, r = self.get(s, f'/pub_key?username={username}')
        if status != OK: return status, None
        pub_key = r['ok']
        if 'n' not in pub_key:
            return NOTWORKING, None
        n = int(pub_key['n'], 16)
        return OK, n


class StatusChecker(WebChecker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, checker_tag='status', **kwargs)
    def place_flag(self):
        status, creds = self.get_or_create_user(self.tick)
        if status != OK: return status
        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds, 'handshake': handshake})
        if status != OK: return status
        flag = self.get_flag(self.tick)
        status, _ = self.post(s, '/set_status', data={
            'status': flag
        })
        if status != OK: return status
        sentence = make_sentence()
        status, r = self.post(s, '/post_message', data={
            'message': json.dumps({
                'encrypted': False,
                'message': sentence.encode('utf-8').hex()
            })
        })
        if status != OK: return status
        return OK

    def check_flag(self, tick):
        status, creds = self.get_or_create_user(tick, create=False)
        if status != OK: return status
        s = requests.Session()
        status, _ = self.post(s, '/login', data=creds)
        if status != OK: return status
        status, r = self.get(s, '/status')
        if status != OK: return NOTWORKING
        flag_check = r['ok']
        self.logger.info(f'Found flag {flag_check} vs {self.get_flag(tick)}')
        if self.get_flag(tick) != flag_check:
            return NOTFOUND
        return OK

    def check_service(self):
        # Basic check for web interface
        s = requests.Session()
        status, _ = self.get(s, '/', json=False)
        if status != OK: return status
        status, _ = self.get(s, '/static/main.js', json=False)
        if status != OK: return status
        # Check for login / session active
        status, creds = self.get_or_create_user(self.tick)
        if status != OK: return status
        s = requests.Session()
        status, _ = self.post(s, '/login', data=creds) # read-only (no handshake)
        if status != OK: return status
        cookies = s.cookies.get_dict()
        if not 'session_id' in cookies:
            self.logger.warn(f'No session_id in cookies')
            return NOTWORKING
        if not cookies['session_id'].startswith('SID'):
            self.logger.warn(f'Cookie does not start with SID {cookies["session_id"]}')
            return NOTWORKING
        sess_id_prefix = cookies['session_id'][3:3+6]
        self.logger.info(f'Looking for my sess id prefix {sess_id_prefix}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._ip, MONITOR_PORT))
        data = b''
        while True:
            chunk = s.recv(4096)
            if chunk == b'': break
            data += chunk
        data = data.decode('utf-8')
        lines = data.split('\n')
        for line in lines:
            if sess_id_prefix in line: return OK
        return NOTWORKING


class MessageChecker(WebChecker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, checker_tag='message', **kwargs)
    def place_flag(self):
        status, creds = self.get_or_create_user(self.tick)
        if status != OK: return status
        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds, 'handshake': handshake})
        if status != OK: return status
        flag = self.get_flag(self.tick)
        status, r = self.post(s, '/post_message', data={
            'message': json.dumps({
                'encrypted': True,
                'message': flag.encode('utf-8').hex()
            })
        })
        if status != OK: return status
        if not 'token' in r: return NOTWORKING
        ident = self.make_ident('token1', self.tick)
        self.store_blob(ident, r['token'].encode('utf-8'))
        return OK

    def check_flag(self, tick):
        ident = self.make_ident('token1', tick)
        token = self.retrieve_blob(ident).decode('utf-8')
        if token is None or token == b'':
            self.logger.warn(f'Token not found for ident, probably missed tick')
            return NOTFOUND
        status, creds = self.get_or_create_user(tick, create=False)
        if status != OK: return status
        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds, 'handshake': handshake})
        if status != OK: return status
        status, (d,n) = self.get_priv_key(s)
        if status != OK: return status
        status, r = self.get(s, '/broadcast_messages')
        if status != OK: return status
        messages = r['ok']
        for message in messages:
            if message.get('token') != token: continue
            flag_message = message
            break
        else:
            return NOTFOUND
        if flag_message.get('author') != creds['username']:
            return NOTWORKING
        if not flag_message.get('encrypted', False):
            return NOTWORKING
        status, flag_check = decrypt_message(flag_message, 1, d, n, logger=self.logger)
        if status != OK: return status
        flag_check = flag_check.decode('utf-8')
        if self.get_flag(tick) != flag_check:
            self.logger.error(f'Failed to decrypt flag, got {flag_check} vs {self.get_flag(tick)}')
            return NOTFOUND
        return OK

    def check_service(self):
        status, creds = self.get_or_create_user(self.tick)
        if status != OK: return status
        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds, 'handshake': handshake})
        if status != OK: return status
        sentence = make_sentence()
        status, r = self.post(s, '/post_message', data={
            'message': json.dumps({
                'encrypted': False,
                'message': sentence.encode('utf-8').hex()
            })
        })
        if status != OK: return status
        if not 'token' in r: return NOTWORKING
        token = r['token']
        status, r = self.get(s, '/broadcast_messages')
        if status != OK: return status
        messages = r['ok']
        for message in messages:
            if message.get('token') != token: continue
            my_message = message
            break
        else:
            return NOTFOUND
        if my_message.get('author') != creds['username']:
            return NOTWORKING
        if my_message.get('encrypted') != False:
            return NOTWORKING
        if my_message.get('message') != sentence.encode('utf-8').hex():
            self.logger.error(f'Message did not match {my_message.get("message")} '
                              f'vs {sentence.encode("utf-8").hex()}')
            return NOTWORKING
        return OK

class ThreeMessageChecker(WebChecker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, checker_tag='message3', **kwargs)
    def place_flag(self):
        status, creds1 = self.get_or_create_user(self.tick, tag='1')
        if status != OK: return status
        status, creds2 = self.get_or_create_user(self.tick, tag='2')
        if status != OK: return status
        status, creds3 = self.get_or_create_user(self.tick, tag='3')
        if status != OK: return status
        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds1, 'handshake': handshake})
        if status != OK: return status
        flag = self.get_flag(self.tick)
        status, r = self.post(s, '/post_message', data={
            'message': json.dumps({
                'encrypted': True,
                'message': flag.encode('utf-8').hex(),
                'recipients': [creds2['username'], creds3['username']]
            })
        })
        if status != OK: return status
        if not 'token' in r: return NOTWORKING
        ident = self.make_ident('token1', self.tick)
        self.store_blob(ident, r['token'].encode('utf-8'))
        return OK

    def check_flag(self, tick):
        token = self.retrieve_blob(self.make_ident('token1', tick)).decode('utf-8')
        if token is None or token == b'':
            self.logger.warn(f'Token not found for ident, probably missed tick')
            return NOTFOUND
        status, creds1 = self.get_or_create_user(tick, create=False, tag='1')
        if status != OK: return status
        status, creds2 = self.get_or_create_user(tick, create=False, tag='2')
        if status != OK: return status
        status, creds3 = self.get_or_create_user(tick, create=False, tag='3')
        if status != OK: return status
        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds1, 'handshake': handshake})
        if status != OK: return status
        status, (d,n) = self.get_priv_key(s)
        if status != OK: return status
        status, r = self.get(s, '/broadcast_messages')
        if status != OK: return status
        messages = r['ok']
        for message in messages:
            if message.get('token') != token: continue
            flag_message = message
            break
        else:
            return NOTFOUND
        if flag_message.get('author') != creds1['username']:
            return NOTWORKING
        if not flag_message.get('encrypted', False):
            return NOTWORKING
        status, flag_check = decrypt_message(flag_message, 3, d, n, logger=self.logger)
        if status != OK: return status
        flag_check = flag_check.decode('utf-8')
        if self.get_flag(tick) != flag_check:
            self.logger.error(f'Failed to decrypt flag, got {flag_check} vs {self.get_flag(tick)}')
            return NOTFOUND
        return OK

    def check_service(self):
        status, creds1 = self.get_or_create_user(self.tick, create=False, tag='1')
        if status != OK: return status
        status, creds2 = self.get_or_create_user(self.tick, create=False, tag='2')
        if status != OK: return status
        status, creds3 = self.get_or_create_user(self.tick, create=False, tag='3')
        if status != OK: return status
        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds1, 'handshake': handshake})
        if status != OK: return status
        sentence = make_sentence()
        status, r = self.post(s, '/post_message', data={
            'message': json.dumps({
                'encrypted': True,
                'message': sentence.encode('utf-8').hex(),
                'recipients': [creds2['username'], creds3['username']]
            })
        })
        if status != OK: return status
        if not 'token' in r: return NOTWORKING
        token = r['token']
        status, r = self.get(s, '/broadcast_messages')
        if status != OK: return status
        messages = r['ok']
        for message in messages:
            if message.get('token') != token: continue
            my_message = message
            break
        else:
            return NOTFOUND
        if my_message.get('author') != creds1['username']:
            return NOTWORKING
        if my_message.get('encrypted') != True:
            return NOTWORKING
        if set(my_message.get('recipients')) != set([creds2['username'], creds3['username']]):
            self.logger.error(f'Incorrect recipients list {my_message.get("recipients")}')
            return NOTWORKING

        # try to decrypt all three ways
        status, n1_check = self.get_pub_key(s, creds1['username'])
        if status != OK: return status
        status, n2_check = self.get_pub_key(s, creds2['username'])
        if status != OK: return status
        status, n3_check = self.get_pub_key(s, creds3['username'])
        if status != OK: return status


        status, (d1,n1) = self.get_priv_key(s)
        if status != OK: return status
        if n1_check != n1: return NOTWORKING
        status, sentence_check = decrypt_message(my_message, 3, d1, n1, logger=self.logger)
        if status != OK: return status
        if sentence_check != sentence.encode('utf-8'):
            self.logger.error(f'Message did not match {sentence_check} '
                              f'vs {sentence.encode("utf-8")}')
            return NOTWORKING

        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds2, 'handshake': handshake})
        if status != OK: return status
        status, (d2,n2) = self.get_priv_key(s)
        if status != OK: return status
        if n2_check != n2: return NOTWORKING
        status, sentence_check = decrypt_message(my_message, 3, d2, n2, logger=self.logger)
        if status != OK: return status
        if sentence_check != sentence.encode('utf-8'):
            self.logger.error(f'Message did not match {sentence_check} '
                              f'vs {sentence.encode("utf-8")}')
            return NOTWORKING

        s = requests.Session()
        handshake = random.choices(string.ascii_lowercase + string.digits, k=10)
        status, _ = self.post(s, '/login', data={**creds3, 'handshake': handshake})
        if status != OK: return status
        status, (d3,n3) = self.get_priv_key(s)
        if status != OK: return status
        if n3_check != n3: return NOTWORKING
        status, sentence_check = decrypt_message(my_message, 3, d3, n3, logger=self.logger)
        if status != OK: return status
        if sentence_check != sentence.encode('utf-8'):
            self.logger.error(f'Message did not match {sentence_check} '
                              f'vs {sentence.encode("utf-8")}')
            return NOTWORKING

        return OK
