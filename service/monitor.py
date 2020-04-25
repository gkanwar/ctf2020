### Small socket server to deliver list of logged in users.

import json
import socketserver
import sys
import urllib.request
from http.client import HTTPConnection
# Do a little hacking
HTTPConnection._encode_request = lambda self, r: r.encode('utf-8')

class MonitorHandler(socketserver.StreamRequestHandler):
    WEB_PORT = None
    def handle(self):
        r = urllib.request.urlopen(f'http://localhost:{WEB_PORT}/🙃', timeout=1)
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
                self.wfile.write((key[3:] + '\n').encode('utf-8'))

class NonblockingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = int(sys.argv[1])
    WEB_PORT = int(sys.argv[2])
    MonitorHandler.WEB_PORT = WEB_PORT
    with NonblockingServer((HOST, PORT), MonitorHandler) as server:
        server.serve_forever()
