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
MAX_CONTENT_LENGTH = 1024*1024
STATIC_DIR = './static/'

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
    def send_generic_headers(self):
        self.send_headers({
            'Date': get_utc_timestamp(),
            'Connection': 'keep-alive'
        })
    def end_headers(self):
        self.write_str('\r\n')

    def send_error(self, status_code, reason):
        self.status_line(status_code, reason)
        self.send_headers({'Connection': 'close'})
        self.write_str('\r\n')
        return False # don't keep alive
    def send_text_content(self, content, content_type):
        self.status_line(200, 'OK')
        self.send_generic_headers()
        self.send_headers({
            'Content-Type': f'{content_type}; charset=UTF-8',
            'Content-Length': len(content)
        })
        self.end_headers()
        self.write_str(content)
        return True # keep alive
    def send_file_content(self, fname):
        self.status_line(200, 'OK')
        self.send_generic_headers()
        content_type = 'text/plain; charset=UTF-8'
        if fname.endswith('.css'):
            content_type = 'text/css'
        elif fname.endswith('.js'):
            content_type = 'text/js'
        elif fname.endswith('.html'):
            content_type = 'text/html'
        elif fname.endswith('.jpg'):
            content_type = 'image/jpeg'
        if content_type.startswith('text/plain'):
            with open(fname, 'r') as f:
                content = f.read()
        else:
            with open(fname, 'rb') as f:
                content = f.read()
        self.send_headers({
            'Content-Type': content_type,
            'Content-Length': len(content)
        })
        self.end_headers()
        if isinstance(content, str):
            self.write_str(content)
        else:
            self.wfile.write(content)
        return True # keep alive


    def read_body(self, headers):
        if 'Content-Length' not in headers: return b''
        try:
            content_length = int(headers['Content-Length'])
        except ValueError:
            return self.send_error(400, 'Bad Request')
        if content_length > MAX_CONTENT_LENGTH:
            return self.send_error(400, 'Bad Request')
        content = b''
        while len(content) < content_length:
            chunk = self.rfile.read(content_length - len(content))
            if len(chunk) == 0:
                return self.send_error(400, 'Bad Request')
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
            name = name[:-1] # strip :
            headers[name] = value
        else: # too many headers
            return self.send_error(400, 'Bad Request')
        body = self.read_body(headers)
        if body == False: return False
        logger.info(f'{method} {path} (from {self.client_address[0]})')
        if method == 'GET':
            return self.get(path, headers=headers, body=body)
        elif method == 'POST':
            return self.post(path, headers=headers, body=body)
        else:
            return self.send_error(405, 'Method Not Allowed')
        
    def handle(self):
        try:
            keep_alive = True
            while keep_alive:
                keep_alive = self.handle_http()
        except Exception as e:
            self.send_error(500, 'Internal Server Error')
            logger.exception('Fatal error in handle()')
        logger.info('Request handled, exiting')

    def get_static(self, subpath):
        if '..' in subpath:
            return self.send_error(403, 'Forbidden')
        fname = STATIC_DIR + subpath
        if not os.path.isfile(fname):
            return self.send_error(404, 'Not Found')
        return self.send_file_content(fname)
        
    def get(self, path, *, headers, body):
        # for our friends
        if path == '/🙃':
            return self.send_text_content(
                'Hello friend, have some env vars:\n'
                + json.dumps(dict(os.environ)) + '\n', 'text/plain')
        path = urllib.parse.unquote(path)
        path = path.split('#', 1)[0]
        if not '?' in path: path += '?'
        path, query = path.split('?', 1)
        if not path.startswith('/'):
            return self.send_error(404, 'Not Found')
        if path.startswith('/static'):
            subpath = path[7:]
            return self.get_static(subpath)
        if path == '/':
            return self.send_text_content("""
            <html>
            <body>
            Hello, world!
            </body>
            </html>""", 'text/html')
        else:
            return self.send_error(404, 'Not Found')

    def post(self, path, *, headers, body):
        # FORNOW
        return self.send_error(405, 'Method Not Allowed')

class NonblockingWebserver(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = int(sys.argv[1])
    with NonblockingWebserver((HOST, PORT), Webhandler) as server:
        logger.info(f'Server bound to localhost:{PORT}')
        server.serve_forever()
