import time
from auth import check_username, check_login, register_user
from log import logger
from user import list_users, User
from message import save_message, list_broadcasted, list_received

def post_api(*args, send_error, **kwargs):
    try:
        return _post_api(*args, send_error=send_error, **kwargs)
    except Exception as e:
        logger.exception(f'POST api fatal error')
        return send_error(500, 'Internal Server Error')

def _post_api(path, query, session, *, send_json, send_error):
    if path == '/login':
        if 'username' not in query:
            return send_json({'error': 'No username'})
        if 'password' not in query:
            return send_json({'error': 'No password'})
        success, reason = check_login(query['username'], query['password'])
        if not success:
            return send_json({'error': reason})
        session.activate_login(query['username'], query.get('handshake'))
        return send_json({'ok': reason})
    elif path == '/register':
        if 'username' not in query:
            return send_json({'error': 'No username'})
        if 'password' not in query:
            return send_json({'error': 'No password'})
        success, reason = register_user(query['username'], query['password'])
        if not success:
            return send_json({'error': reason})
        # also login
        session.activate_login(query['username'], query.get('handshake'))
        return send_json({'ok': reason})
    elif path == '/post_message':
        if 'message' not in query:
            return send_json({'error': 'No message'})
        try:
            message = json.loads(query['message'])
        except:
            return send_json({'error': 'Bad message format'})
        message_keys = ['recipients', 'encrypted', 'message']
        if not set(message_keys) <= set(message):
            return send_json({'error': 'Bad message format'})
        message = {k: message[k] for k in message_keys}
        if not isinstance(message['recipients'], list):
            return send_json({'error': 'Bad message format'})
        rs = message['recipients']
        for r in rs:
            if not check_username(r):
                return send_json({'error': 'Bad message format'})
        message['encrypted'] = bool(message['encrypted'])
        message['timestamp'] = time.time()
        token = save_message(message)
    elif path == '/set_status':
        if 'status' not in query:
            return send_json({'error': 'No status'})
        if not session:
            return send_json({'error': 'Login first'})
        if not session.set_persist('status', query['status']):
            return send_json({'error': 'Status write failed'})
        return send_json({'ok': 'Status updated'})
    else:
        return send_error(404, 'Not Found')

def get_api(*args, send_error, **kwargs):
    try:
        return _get_api(*args, send_error=send_error, **kwargs)
    except Exception as e:
        logger.exception(f'GET api fatal error')
        return send_error(500, 'Internal Server Error')

def _get_api(path, query, session, *, send_json, send_error):
    if path == '/status':
        if not session:
            return send_json({'error': 'Not logged in'})
        return send_json({'ok': session.get('status')})
    elif path == '/status_all':
        users = list_users()
        out = []
        for username in users:
            u = User(username)
            status = u.get('status')
            if status is not None:
                out.append({'username': username, 'status': status})
        return send_json({'ok': out})
    elif path == '/priv_key':
        if not session:
            return send_json({'error': 'Not logged in'})
        if not session.privileged:
            return send_json({'error': 'Not privileged session'})
        return send_json({'ok': session.get('priv_key')})
    elif path == '/pub_key':
        if 'username' not in query:
            return send_json({'error': 'No username'})
        ### INTERNAL NOTE: unsanitized username
        u = User(query['username'])
        pub_key = u.get('pub_key')
        if pub_key is None:
            return send_json({'error': 'No pub key found'})
        return send_json({'ok': session.get('pub_key')})
    elif path == '/broadcast_messages':
        return send_json({'ok': list_broadcasted()})
    elif path == '/messages':
        if not session:
            return send_json({'error': 'Not logged in'})
        return send_json({'ok': list_received(session.get('username'))})
    else:
        return send_error(404, 'Not Found')
