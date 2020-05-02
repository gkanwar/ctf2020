### INTERNAL NOTE: This file is "lost", so user only gets the .pyc

import logging
logger = logging.getLogger('monitor')
import json
import socketserver
import urllib.request
from http.client import HTTPConnection
# Do a little hacking
HTTPConnection._encode_request = lambda self, r: r.encode('utf-8')

class MonitorHandler(socketserver.StreamRequestHandler):
    WEB_PORT = None
    def handle(self):
        logger.info(f'Monitor request from {self.client_address[0]}:{self.client_address[1]}')
        r = urllib.request.urlopen(f'http://localhost:{MonitorHandler.WEB_PORT}/🙃', timeout=1)
        if r.status != 200:
            self.wfile.write(b'Internal error!\n')
            return
        body = r.read().decode('utf-8')
        lines = body.split('\n')
        if len(lines) < 2:
            self.wfile.write(b'Internal error!\n')
            return
        env = json.loads(lines[1])
        count = 0
        for key in env:
            if key.startswith('SID'):
                count += 1
                self.wfile.write((f'{key[3:3+6]} {env[key]}' + '\n').encode('utf-8'))
        logger.info(f'Sent info about {count} sessions')

class NonblockingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_monitor(host, port, web_port):
    MonitorHandler.WEB_PORT = web_port
    with NonblockingServer((host, port), MonitorHandler) as server:
        server.serve_forever()
