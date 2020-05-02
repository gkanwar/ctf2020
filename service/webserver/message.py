from Crypto.Cipher import AES
import glob
import json
import os
import random
import string
from aes import pad
from log import logger
from user import RSA_BITS, RSA_E

RSA_BYTES = RSA_BITS // 8
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

def rsa_encrypt(pub_key, bs):
    m = int.from_bytes(bs, byteorder='big')
    n = pub_key['n']
    return pow(m, RSA_E, n).to_bytes(RSA_BYTES, byteorder='big')

def encrypt_message(message, *, author):
    # TODO: recipients
    targets = [author.get('pub_key')]
    aes_key = os.urandom(AES.block_size)
    iv = os.urandom(AES.block_size)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    encrypted_message = cipher.encrypt(pad(message))
    aes_key_pad = aes_key + os.urandom(RSA_BYTES - AES.block_size)
    encrypted_key = b''.join([rsa_encrypt(rsa_key, aes_key_pad) for rsa_key in targets])
    full_encrypted_message = encrypted_key + iv + encrypted_message
    return full_encrypted_message
        
def list_broadcasted():
    all_messages = _load_messages()
    return [m for m in all_messages if m.get('recipients') is None]

def list_received(username):
    all_messages = _load_messages()
    return [m for m in all_messages if username in m.get('recipients', [])]
