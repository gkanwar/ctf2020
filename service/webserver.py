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

from api import post_api
from session import Session

MAX_HEADERS = 1024
MAX_CONTENT_LENGTH = 1024*1024
STATIC_DIR = './static/'
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger('webserver')

def get_utc_timestamp():
    now = time.mktime(datetime.datetime.now().timetuple())
    return wsgihandlers.format_date_time(now)

def parse_path(path):
    if not '?' in path: path += '?'
    path = path.split('#', 1)[0]
    path, query = path.split('?', 1)
    path = urllib.parse.unquote(path)
    query = parse_query(query)
    return path, query

def parse_query(query):
    bits = query.split('&')
    out = {}
    for bit in bits:
        if '=' not in bit: continue
        name, value = bit.split('=', 1)
        name = urllib.parse.unquote(name)
        value = urllib.parse.unquote(value)
        out[name] = value
    return out

def parse_form_data_chunk(chunk):
    try:
        headers = {}
        header_section, form_value = chunk.split(b'\r\n\r\n', 1)
        header_section = header_section.decode('utf-8')
        for line in header_section.split('\r\n'):
            line = line.strip()
            if line == '': continue
            name, value = line.split(': ', 1)
            headers[name] = value
        if not 'Content-Disposition' in headers:
            logger.error('No Content-Disposition for form data')
            return {}
        disp = headers['Content-Disposition']
        bits = disp.split('; ')
        if len(bits) < 2 or bits[0] != 'form-data':
            logger.error('Bad Content-Disposition for form data')
            return {}
        form_info = bits[1]
        if not '=' in form_info:
            logger.error('Bad Content-Disposition for form data')
            return {}
        key, value = form_info.split('=')
        if key != 'name' or not value.startswith('"') or not value.endswith('"'):
            logger.error('Bad Content-Disposition for form data')
            return {}
        form_name = value[1:-1]
        # assume text form value
        form_value = form_value.decode('utf-8').strip()
        return {form_name: form_value}
    except Exception as e:
        logger.error(f'Parsing form data failed with error {e}, skipping')
        return {}

def parse_post_body(body, content_type):
    content_type, details = content_type.split('; ', 1)
    if content_type == 'application/x-www-form-urlencoded':
        return parse_query(body)
    elif content_type == 'multipart/form-data':
        if not '=' in details:
            logger.error(f'Bad multipart/xxx spec')
            return {}
        name, value = details.split('=', 1)
        if not name == 'boundary':
            logger.error(f'Bad multipart/xxx spec')
            return {}
        boundary = ('--' + value).encode('utf-8') # why extra hyphens??
        chunks = body.split(boundary)
        if len(chunks) < 3:
            logger.error(f'Bad multipart/xxx data')
            return {}
        chunks = chunks[1:-1]
        form_data = {}
        for chunk in chunks:
            form_data.update(parse_form_data_chunk(chunk))
        logger.info(f'Got post form data = {form_data}')
        return form_data
    else:
        logger.warning(f'Unsupported form data content type {content_type}')
        return {}

class Webhandler(socketserver.StreamRequestHandler):

    def write_str(self, s):
        self.wfile.write(s.encode('utf-8', 'replace'))
    def readline_str(self):
        return self.rfile.readline().decode('utf-8')
    def status_line(self, status_code, reason):
        self.write_str(f'HTTP/1.1 {status_code} {reason}\r\n')
    def send_headers(self, headers):
        for name, val in headers:
            self.write_str(f'{name}: {val}\r\n')
    def send_generic_headers(self):
        headers = [
            ('Date', get_utc_timestamp()),
            ('Connection', 'keep-alive')
        ]
        if self.session:
            for cookie in self.session.get_cookies():
                headers.append(('Set-Cookie', cookie))
        self.send_headers(headers)
    def end_headers(self):
        self.write_str('\r\n')

    def send_error(self, status_code, reason):
        self.status_line(status_code, reason)
        self.send_headers([('Connection', 'close')])
        self.write_str('\r\n')
        return False # don't keep alive
    def send_text_content(self, content, content_type):
        self.status_line(200, 'OK')
        self.send_generic_headers()
        self.send_headers([
            ('Content-Type', f'{content_type}; charset=UTF-8'),
            ('Content-Length', len(content))
        ])
        self.end_headers()
        self.write_str(content)
        return True # keep alive
    def send_json_content(self, content):
        return self.send_text_content(json.dumps(content)+'\n', 'application/json')
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
        self.send_headers([
            ('Content-Type', content_type),
            ('Content-Length', len(content))
        ])
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

    def parse_cookies(self, headers):
        if not 'Cookie' in headers:
            return {}
        cookie_str = headers['Cookie']
        cookie_list = cookie_str.split('; ')
        cookies = {}
        for cookie in cookie_list:
            if not '=' in cookie: continue
            name, value = cookie.split('=', 1)
            cookies[name] = value
        return cookies

    def handle_http(self):
        request_line = self.readline_str().strip()
        tokens = request_line.split()
        if len(tokens) != 3: return False
        method, path, protocol = tokens
        headers = {}
        for i in range(MAX_HEADERS):
            header_line = self.readline_str().strip()
            if header_line == '': break
            name, value = header_line.split(': ', 1)
            headers[name] = value
        else: # too many headers
            return self.send_error(400, 'Bad Request')
        body = self.read_body(headers)
        if body == False: return False
        cookies = self.parse_cookies(headers)
        self.session = Session.from_cookies(cookies)
        logger.info(f'{method} {path} (from {self.client_address[0]}) body {len(body)}')
        if method == 'GET':
            return self.get(path, headers=headers, body=body, cookies=cookies)
        elif method == 'POST':
            return self.post(path, headers=headers, body=body, cookies=cookies)
        else:
            return self.send_error(405, 'Method Not Allowed')

    def setup(self):
        super().setup()
        self.session = None

    def handle(self):
        try:
            keep_alive = True
            while keep_alive:
                keep_alive = self.handle_http()
        except Exception as e:
            self.send_error(500, 'Internal Server Error')
            logger.exception('Fatal error in handle()')
        logger.info('Request handled, exiting')

    def finish(self):
        if self.session: self.session.save_store()

    def get_static(self, subpath):
        if '..' in subpath:
            return self.send_error(403, 'Forbidden')
        fname = STATIC_DIR + subpath
        if not os.path.isfile(fname):
            return self.send_error(404, 'Not Found')
        return self.send_file_content(fname)

    def get(self, path, *, headers, body, cookies):
        # for our friends
        if path == '/🙃':
            return self.send_text_content(
                'Hello friend, here is the list of sessions:\n'
                + json.dumps(dict(os.environ)) + '\n', 'text/plain')
        path, query = parse_path(path)
        if not path.startswith('/'):
            return self.send_error(404, 'Not Found')
        if path.startswith('/static'):
            subpath = path[7:]
            return self.get_static(subpath)
        if path == '/':
            return self.get_static('home.html')
        else:
            return self.send_error(404, 'Not Found')

    def post(self, path, *, headers, body, cookies):
        path, _ = parse_path(path)
        if 'Content-Type' in headers:
            query = parse_post_body(body, headers['Content-Type'])
        else:
            query = {}
        return post_api(path, query, self.session,
                        send_json=self.send_json_content, send_error=self.send_error)

class NonblockingWebserver(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = int(sys.argv[1])
    with NonblockingWebserver((HOST, PORT), Webhandler) as server:
        logger.info(f'Server bound to localhost:{PORT}')
        server.serve_forever()
