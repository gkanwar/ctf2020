import sys

t = int(sys.argv[1])
i = int(sys.argv[2])

with open('client.conf.template', 'r') as f:
    template = f.read()

def get_snip(fname, begin_phrase, end_phrase):
    copying = False
    out = ""
    with open(fname, 'r') as f:
        for line in f:
            if begin_phrase in line:
                copying = True
            if copying:
                out += line
            if end_phrase in line:
                return out
    raise RuntimeError('end phrase not found')
            

out = ""
for line in template.split('\n'):
    if 'CA_GOES_HERE' in line:
        ca = get_snip('ca.crt', 'BEGIN CERTIFICATE', 'END CERTIFICATE')
        out += ca
    elif 'CERT_GOES_HERE' in line:
        cert = get_snip('team{}_{}.crt'.format(t, i),
                        'BEGIN CERTIFICATE', 'END CERTIFICATE')
        out += cert
    elif 'KEY_GOES_HERE' in line:
        key = get_snip('team{}_{}.key'.format(t, i),
                       'BEGIN PRIVATE KEY', 'END PRIVATE KEY')
        out += key
    else:
        out += line + '\n'

with open('team{}_{}.conf'.format(t, i), 'w') as f:
    f.write(out)
