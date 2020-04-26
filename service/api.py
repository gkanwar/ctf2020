import logging
from auth import check_login, register_user
from user import list_users, User
logger = logging.getLogger('webserver')

def post_api(*args, send_error, **kwargs):
    try:
        return _post_api(*args, send_error=send_error, **kwargs)
    except Exception as e:
        logger.error(f'POST api fatal error {e}')
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
        logger.error(f'POST api fatal error {e}')
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
            out.append({'username': username, 'status': u.get('status')})
        return send_json({'ok': out})
    else:
        return send_error(404, 'Not Found')
