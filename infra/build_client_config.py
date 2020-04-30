import sys

server_ip = sys.argv[1]
client_prefix = sys.argv[2]

with open('client.conf.template', 'r') as f:
    template = f.read()

with open('team_confs/ca.crt', 'r') as f:
    ca = f.read()
with open(f'team_confs/{client_prefix}.crt', 'r') as f:
    cert = f.read()
with open(f'team_confs/{client_prefix}.key', 'r') as f:
    key = f.read()

with open(f'team_confs/{client_prefix}.conf', 'w') as f:
    f.write(template.format(server_ip, ca, cert, key))
