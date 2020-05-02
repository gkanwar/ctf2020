from Crypto.Cipher import AES

def pad(s):
    padding = AES.block_size - len(s) % AES.block_size
    return s + bytes([padding]*padding)
def unpad(s):
    padding = s[-1]
    assert isinstance(padding, int)
    return s[:-padding]
