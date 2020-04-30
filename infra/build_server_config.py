import sys

t = int(sys.argv[1])

with open('server.conf.template', 'r') as f:
    template = f.read()

with open('team_confs/ca.crt', 'r') as f:
    ca = f.read()
with open(f'team_confs/team{t}_server.crt', 'r') as f:
    cert = f.read()
with open(f'team_confs/team{t}_server.key', 'r') as f:
    key = f.read()
with open(f'team_confs/dh.pem', 'r') as f:
    dh = f.read()

with open(f'team_confs/team{t}_server.conf', 'w') as f:
    f.write(template.format(ca, cert, key, dh, t))
