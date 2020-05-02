from ctf_gameserver.checker import BaseChecker, OK, TIMEOUT, NOTWORKING, NOTFOUND
import pickle
import random
import requests
import string

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
    
    def place_flag(self):
        username = 'test' + ''.join(random.choices(string.digits , k=16))
        password = ''.join(random.choices(string.printable, k=32))
        creds = {'username': username, 'password': password}
        blob = pickle.dumps(creds)
        ident = f'creds_status_{self._service}_{self._team}_{self.tick}'
        print('saving ident', ident)
        self.store_blob(ident, blob)
        s = requests.Session()
        status, _ = self.post(s, '/register', data=creds)
        if status != OK: return status
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
        ident = f'creds_status_{self._service}_{self._team}_{tick}'
        print('loading ident', ident)
        creds = pickle.loads(self.retrieve_blob(ident))
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
        return OK
