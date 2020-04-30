import glob
import json
import random
import string
from log import logger

MESSAGE_DIR = './private/'
MESSAGE_EXT = '.data'

def save_message(message):
    token = ''.join(random.choices(string.ascii_letters, k=12))
    fname = MESSAGE_DIR + 'post' + str(message['timestamp']) + token + MESSAGE_EXT
    with open(fname, 'w') as fd:
        json.dump(message, fd)
    return token

### INTERNAL NOTE: collision with username files
def _load_messages():
    message_files = glob.glob(MESSAGE_DIR + '*' + MESSAGE_EXT)
    messages = []
    for f in message_files:
        try:
            with open(f, 'r') as fd:
                messages.append(json.load(fd))
        except:
            logger.warning(f'Corrupt message file {f}, skipping', exc_info=True)
    return messages
        
def list_broadcasted():
    all_messages = _load_messages()
    return [m for m in all_messages if m.get('recipients') is None]

def list_received(username):
    all_messages = _load_messages()
    return [m for m in all_messages if username in m.get('recipients', [])]
