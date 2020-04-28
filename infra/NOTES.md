# Notes on VPN server setup


## Set up the CA and certs
On AWS, we can get OpenVPN community edition and easy RSA for the CA
fairly easily:
```
# Setup EPEL
sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
sudo yum-config-manager --enable epel
# Install
sudo yum install openvpn easyrsa
```

Then move easyrsa into the OpenVPN directory
```
sudo mkdir /etc/openvpn/easy-rsa
sudo cp -Rv /usr/share/easy-rsa/3.*/* /etc/openvpn/easy-rsa
```

Generate CA cert
```
cd /etc/openvpn/easy-rsa
sudo ./easyrsa init-pki
sudo ./easyrsa build-ca
```
I chose to specify a CA password, but I think you can skip somehow. We
should also generate DH params.
```
sudo ./easyrsa gen-dh
```

Next, generate all the certs we need. First the server.
```
sudo ./easyrsa gen-req <server name> nopass
```
I didn't use a passphrase for this or client keys, since it's one time
use and that's extra info to pass around.

Client certs, for each team server and team player.
```
sudo ./easyrsa gen-req <client name> nopass
```

Finally, sign all the cert requests using our CA.
```
sudo ./easyrsa sign-req server <server name>
sudo ./easyrsa sign-req client <client name>
# ...
```


## Set up the OpenVPN confs
The installed openvpn server comes with templates.
```
sudo cp /usr/share/doc/openvpn-*/sample/sample-config-files/server.conf /etc/openvpn/
```
In the config, I tweaked several things. Importantly, we have to point
to the ca, server cert and key, and DH params. For the CTF setup, it
is also useful to assign each client specific IPs, so we need to
enable the CCD and create config files with
`ifconfig-push <client ip> <client endpoint ip>` directives in it. The
default setup for the server assigns a pool of dynamically allocated
IPs and gives the first to the server. It's nice to have slightly more
control, so we can break out the translation of that macro and be
picky.
```
mode server
tls-server
ifconfig <server ip> <server ip peer> # not sure what the peer does
route <ip prefix> <subnet mask> # for the whole private subnet
push "route <ip prefix> <subnet mask>" # whole private subnet
# NOTE: leave client-to-client commented, we will use iptables
```


## Set up the client confs
The client needs to know how to talk to this OpenVPN server. We need
the `*.crt` and `*.key` files in `easy-rsa/pki/issued/*` and
`easy-rsa/pki/private/*`. Use these files to fill in the template
```
# Run with sudo openvpn --config <this file>

client
dev tun
proto udp
remote <openvpn server public ip> 1194
resolv-retry infinite
nobind
persist-key
persist-tun

<ca>
CA_GOES_HERE
</ca>
<cert>
CERT_GOES_HERE
</cert>
<key>
KEY_GOES_HERE
</key>

remote-cert-tls server

cipher AES-256-CBC
verb 3
```


## Set up routing and NAT
Since we also want to use NAT and turn client routing ono/off easily,
it's better to use the IP-level routing instead of `client-to-client`
from OpenVPN. With `client-to-client` disabled, incoming requests
should already go to the IP layer, and for example pinging the OpenVPN
private subnet IP address from clients should work.

By default, `ip_forward` is probably disabled and clients can't see
each other yet. This can be solved by adding to
`/etc/sysctl.d/<name>.conf`.
```
net.ipv4.ip_forward=1
```
Then reload the conf
```
sudo sysctl -p /etc/sysctl.d/<name>.conf
```

Now clients should all be able to talk to each other freely. However,
there is no NAT yet, and this also enabled forwarding on all
interfaces. Probably best to avoid that, so I fiddled with
iptables. Setup the NAT and drop ip forwarding in the first place.
```
sudo iptables -A FORWARD -j DROP
sudo iptables -t nat -A POSTROUTING -s 10.10.0.0/16 -d 10.10.0.0/16 -j MASQUERADE
```
When the time is right, we can allow the clients to talk with
forwarding on the tun0 interface
```
sudo iptables -I FORWARD 1 -i tun0 -o tun0 -j ACCEPT
```

I messed up a lot, and printing/flushing the tables is useful for
experimenting.
```
sudo iptables -t <table> -nL # print it
sudo iptables -t <table> -F # flush it
```
