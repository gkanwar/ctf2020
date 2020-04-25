from auth import check_login, register_user

def post_api(path, query, session, *, send_json, send_error):
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
        if not session.set('status', query['status']):
            return send_json({'error': 'Status write failed'})
        return send_json({'ok': 'Status updated'})
    else:
        return send_error(404, 'Not Found')
