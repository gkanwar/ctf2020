#!/usr/bin/env python3

import datetime
import json
import logging
import os
import socketserver
import sys
import time
import urllib.parse
import wsgiref.handlers as wsgihandlers
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger('webserver')

MAX_HEADERS = 1024

def get_utc_timestamp():
    now = time.mktime(datetime.datetime.now().timetuple())
    return wsgihandlers.format_date_time(now)

class Webhandler(socketserver.StreamRequestHandler):

    def write_str(self, s):
        self.wfile.write(s.encode('utf-8', 'replace'))
    def readline_str(self):
        return self.rfile.readline().decode('utf-8')
    def status_line(self, status_code, reason):
        self.write_str(f'HTTP/1.1 {status_code} {reason}\r\n')
    def send_headers(self, headers):
        for name in headers:
            val = headers[name]
            self.write_str(f'{name}: {val}\r\n')
        self.write_str('\r\n')

    def read_body(self, headers):
        if 'Content-Length' not in headers: return b''
        try:
            content_length = int(headers['Content-Length'])
        except ValueError:
            self.status_line(400, 'Bad Request')
            return
        if content_length > MAX_CONTENT_LENGTH:
            self.status_line(400, 'Bad Request')
            return None
        content = ''
        while len(content) < content_length:
            chunk = self.rfile.read(content_length - len(content))
            if len(chunk) == 0:
                self.status_line(400, 'Bad Request')
                return None
            content += chunk
        return content

    def handle_http(self):
        request_line = self.readline_str().strip()
        tokens = request_line.split()
        if len(tokens) != 3: return False
        method, path, protocol = tokens
        headers = {}
        for i in range(MAX_HEADERS):
            header_line = self.readline_str().strip()
            if header_line == '': break
            name, value = header_line.split(' ', 1)
            headers[name] = value
        else: # too many headers
            self.status_line(400, 'Bad Request')
        body = self.read_body(headers)
        if body is None: return False
        logger.info(f'{method} {path} (from {self.client_address[0]})')
        if method == 'GET':
            self.get(path, headers=headers, body=body)
        elif method == 'POST':
            self.post(path, headers=headers, body=body)
        else:
            self.status_line(405, 'Method Not Allowed')
        return True
        
    def handle(self):
        print('handle', self.request)
        try:
            keep_alive = True
            while keep_alive:
                keep_alive = self.handle_http()
        except Exception as e:
            self.status_line(500, 'Internal Server Error')
            logger.exception('Fatal error in handle()')
        logger.info('Request handled, exiting')

    def send_text_content(self, content, content_type):
        self.status_line(200, 'OK')
        self.send_headers({
            'Date': get_utc_timestamp(),
            'Content-Type': f'{content_type}; charset=UTF-8',
            'Content-Length': len(content),
            'Connection': 'keep-alive'
        })
        self.write_str(content)

    def get(self, path, *, headers, body):
        # for our friends
        if path == '/🙃':
            self.send_text_content(
                'Hello friend, have some env vars:\n'
                + json.dumps(dict(os.environ)) + '\n', 'text/plain')
            return
        path = urllib.parse.unquote(path)
        path = path.split('#', 1)[0]
        if not '?' in path: path += '?'
        path, query = path.split('?', 1)
        if path == '/':
            self.send_text_content("""
            <html>
            <body>
            Hello, world!
            </body>
            </html>""", 'text/html')
        else:
            self.status_line(404, 'Not Found')
    def post(self, path, *, headers, body):
        # FORNOW
        self.status_line(405, 'Method Not Allowed')

class NonblockingWebserver(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = int(sys.argv[1])
    with NonblockingWebserver((HOST, PORT), Webhandler) as server:
        logger.info(f'Server bound to localhost:{PORT}')
        server.serve_forever()
