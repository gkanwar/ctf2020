from Crypto.Cipher import AES
import glob
import json
import os
import random
import string
from aes import pad
from log import logger
from user import RSA_BITS, RSA_E, User

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
def rsa_decrypt(priv_key, bs):
    m = int.from_bytes(bs, byteorder='big')
    n = priv_key['n']
    d = priv_key['d']
    print('n =', n)
    print('d =', d)
    return pow(m, d, n).to_bytes(RSA_BYTES, byteorder='big')

def encrypt_message(message, *, author, recipients):
    rs = [User(r) for r in recipients]
    targets = [author.get('pub_key')] + [r.get('pub_key') for r in rs]
    print('targets', targets)
    aes_key = os.urandom(AES.block_size)
    print('Dec key =', aes_key.hex())
    iv = os.urandom(AES.block_size)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    encrypted_message = cipher.encrypt(pad(message))
    aes_key_pad = b'\x00'*(2*AES.block_size) + aes_key*2 + os.urandom(RSA_BYTES - 4*AES.block_size)
    print('AES key pad =', aes_key_pad.hex())
    encrypted_keys = [rsa_encrypt(rsa_key, aes_key_pad) for rsa_key in targets]
    ### CHECK
    print('Encrypted message format:')
    for k in encrypted_keys:
        print('Enc key =', k.hex())
    print('iv =', iv.hex())
    print('Enc message =', encrypted_message.hex())
    for enc_key,r in zip(encrypted_keys, [author] + rs):
        assert rsa_decrypt(r.get('priv_key'), enc_key) == aes_key_pad, \
            (f'Decrypt failed for user {r.username}:' '\n'
             f'{rsa_decrypt(r.get("priv_key"), enc_key).hex()}' '\nvs\n'
             f'{aes_key_pad.hex()}')
    ### END CHECK
    full_encrypted_message = b''.join(encrypted_keys) + iv + encrypted_message
    return full_encrypted_message
        
def list_broadcasted():
    all_messages = _load_messages()
    return [m for m in all_messages if m.get('recipients', []) == []]

def list_received_or_sent(username):
    all_messages = _load_messages()
    return [m for m in all_messages
            if (
                    username in m.get('recipients', []) or
                    m.get('recipients', []) != [] and username == m.get('author')
            )]
