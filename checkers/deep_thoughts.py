from ctf_gameserver.checker import BaseChecker, OK, TIMEOUT, NOTWORKING, NOTFOUND
import pickle
import random
import requests
import socket
import string

MONITOR_PORT = 7778

class StatusChecker(BaseChecker):
    def __init__(self, tick, team, service, ip):
        super().__init__(tick, team, service, ip)
        self._prefix = f'http://{ip}'

    def req(self, s, method, path, *, data, timeout):
        method = getattr(s, method)
        r = method(self._prefix + path, data=data, timeout=timeout)
        if r.status_code != 200:
            self.logger.error(f'{path} status code {r.status_code}')
            return NOTWORKING, None
        try:
            j = r.json()
        except ValueError as e:
            self.logger.error('JSON decoding exception', exc_info=True)
            return NOTWORKING, None
        if not 'ok' in j:
            self.logger.error(f'{path} bad JSON response: {j}')
            return NOTWORKING, None
        return OK, j
    def post(self, s, path, *, data, timeout=10):
        return self.req(s, 'post', path, data=data, timeout=timeout)
    def get(self, s, path, *, timeout=10):
        return self.req(s, 'get', path, data=None, timeout=timeout)

    def get_or_create_user(self, tick, *, create=True):
        ident = f'creds_status_{self._service}_{self._team}_{tick}'
        blob = self.retrieve_blob(ident)
        if blob is not None:
            return OK, pickle.loads(blob)
        self.logger.info(f'Did not find user for tick {tick} with ident {ident}, creating...')
        if not create:
            raise RuntimeError(f'User blob should already exist with ident {ident}')
        username = 'test' + ''.join(random.choices(string.digits , k=16))
        password = ''.join(random.choices(string.printable, k=32))
        creds = {'username': username, 'password': password}
        s = requests.Session()
        status, _ = self.post(s, '/register', data=creds)
        if status != OK: return status, None
        blob = pickle.dumps(creds)
        self.store_blob(ident, blob)
        return OK, creds

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
