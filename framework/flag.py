### Utils for flags

import random
import re
import string

def flag_match(flag):
    return re.match(r'flag\{[a-zA-Z]{32}\}', flag)

def make_flag():
    return 'flag{' + ''.join(random.choices(string.ascii_letters, k=32)) + '}'

if __name__ == '__main__':
    flag = make_flag()
    print(make_flag())
    print(bool(flag_match(flag)))
