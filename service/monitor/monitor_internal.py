### INTERNAL NOTE: This file is "lost", so user only gets the .pyc

import json
import socketserver
import urllib.request
from http.client import HTTPConnection
# Do a little hacking
HTTPConnection._encode_request = lambda self, r: r.encode('utf-8')

class MonitorHandler(socketserver.StreamRequestHandler):
    WEB_PORT = None
    def handle(self):
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
        for key in env:
            if key.startswith('SID'):
                self.wfile.write((f'{key[3:3+6]} {env[key]}' + '\n').encode('utf-8'))

class NonblockingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_monitor(host, port, web_port):
    MonitorHandler.WEB_PORT = web_port
    with NonblockingServer((host, port), MonitorHandler) as server:
        server.serve_forever()
