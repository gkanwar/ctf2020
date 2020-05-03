from Crypto.Cipher import AES

# https://en.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm
def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

def int_cube_root(x):
    if x == 1: return x
    low = 1
    high = x
    while True:
        mid = (low + high) // 2
        if mid == low:
            raise RuntimeError('No integer cube root!')
        if mid**3 > x:
            high = mid
        elif mid**3 < x:
            low = mid
        else:
            return mid

def unpad(s):
    padding = s[-1]
    assert isinstance(padding, int)
    return s[:-padding]

### Example data from NOP team
u1 = 'test0402408088354174'
u2 = 'test2990131781082952'
u3 = 'test2743098484005192'

n1 = int('a0d9c984b6c87d4e172dbbe8382efca44736b285ad004a73a2c17e606376b0994d23ff583a1df32aa583b5d696c616db70e59dfee4a8f9b01017c7f13edc14f51b634b6135ba320e7aac6d3bd26ce3a3012ccc78f7cd1e35f2d0c0f482e454adf5e37f9f416891531ce1d07bc32b94f041faa3657978ee995fd77044bd3ed0a3', 16)
n2 = int('c7c3d3c1cb60637f5f71cfe2dfa62f18ae4bbe05edcc952237a014a42974b53b321db53dffb6997105bc92d5b22521fdd35acf6ac177e9aa52ef8a25adb0edd4bef94945c101d13e82f7a26bb98cecf9a499a41859625eb589c1cd22e20eebea7e4a3381dd9617226f9c5f19d8c99435149b8c783eacdc9d0637cfd9cf17c0cb', 16)
n3 = int('9d693503871f2c5ef24c44dadcbc1e2e6c8fe2cc2941ed8c171ad6a9912929011716481c174f606bcb59ce48f240da8add707763806742d40a60b1667c6dac5305b84a0c55c0ca4137fae63d6007b1c92e6eb1e6736d42e4dce71e2396fd20a991ef1bc2230e8586a971b8f0db827437b97caa7e05bcfc32e688725a46363df5', 16)

msg = bytes.fromhex('17e680f49928d1d3da7d3710989f174a69b44a68b3a12e4e25b0b5490e47e43d51742070477e51756194728e0ec6d715959d3599e66ab714fdf4ea115794a2c4436ea215d42c5a150a81726478e967c2e95699313e839a9517f3ea422c44bc2b85792bd29400540ffda67e4cd8d0ef60cf500c491f6203f766fe6312b7de4ce18b8e8a4167aa5c6b922c73c70105166355d5ae5f3ffcc94af864e2b49bb0b230e1dc1b4896cad617ddc38f1802e9e4322ba408c05e73284796766937cf1db0aabd60c7de4dcca38323908d38dfe537007f7ba2715727e1ddf472fb4d0bb43646a919fa60c0b67b575865a6f7c192a8f5bc8373f05e222d94ea0317cd41f8a71222cbc69d87bb05d33fb1a1a0ee2d4c9511b42ac9e174a9b07a6e9e5f424621c8cb6598b0a64fdefd3fd05206abbdf86329426ee986fcf5e81a7cbde1e18d4e67a73874105ca118942422df18d41057b41f79cd03f087ae83cd2d6458c0b624f3e1098e9998a6fcc21920b61a19d388b1cf656e8e0cda2916c8de789feda646e9c2a7e84c3f9f750fd242b57ca2b2ee0555d1fdad816dfdaa5fbfb6fe348de65cf2d2d09265325b45df73876defbe8334e8cd54f7863507ef6c18185288e4134a')

### Attack, see e.g. point 5 of https://crypto.stackexchange.com/a/52520
c1 = int.from_bytes(msg[:128], byteorder='big')
c2 = int.from_bytes(msg[128:2*128], byteorder='big')
c3 = int.from_bytes(msg[2*128:3*128], byteorder='big')
iv = msg[3*128:3*128+16]
enc_text = msg[3*128+16:]

assert egcd(n1, n2)[0] == 1
assert egcd(n1, n3)[0] == 1
assert egcd(n2, n3)[0] == 1

x = c1
n = n1
x = ((modinv(n, n2) * (c2 - x)) % n2) * n + x
n *= n2
x = ((modinv(n, n3) * (c3 - x)) % n3) * n + x
n *= n3


m = int_cube_root(x)
m = m.to_bytes(128, byteorder='big')
print(m.hex())
aes_key = m[32:48]
cipher = AES.new(aes_key, AES.MODE_CBC, iv)
print('Decoded:')
print(unpad(cipher.decrypt(enc_text)).decode('utf-8'))
