#!/bin/bash

### CA lives centrally on the gameserver.
### -- server.{crt,key} for gameserver
### -- teamX.{crt,key} for vulnboxes as ovpn clients to gameserver
### -- teamX_server.{crt,key} for vulnboxes as ovpn servers to members
### -- teamX_Y.{crt,key} for members as ovpn clients to vulnboxes

cd /etc/openvpn/easy-rsa
if [[ "$INIT" == "1" ]]; then # one-time init
    sudo ./easyrsa init-pki
    sudo ./easyrsa build-ca nopass # can add pass if you like feeling secure
fi

if [[ "$NUM_TEAMS" == "" ]]; then
    echo "Must set NUM_TEAMS"
    exit 1
fi
if [[ "$NUM_MEMBERS" == "" ]]; then
    echo "Must set NUM_MEMBERS"
    exit 1
fi
if [[ "$NOP_ID" == "" ]]; then
    echo "Must set NOP_ID"
    exit 1
fi

TEAMS="${NOP_ID} $(seq 1 ${NUM_TEAMS})"

# Generate requests
sudo ./easyrsa --batch --req-cn=server gen-req server nopass
for t in ${TEAMS}; do
    sudo ./easyrsa --batch --req-cn=team${t} gen-req team${t} nopass
    sudo ./easyrsa --batch --req-cn=team${t} gen-req team${t}_server nopass
    for i in $(seq 1 ${NUM_MEMBERS}); do
	sudo ./easyrsa --batch --req-cn=team${t}_${i} gen-req team${t}_${i} nopass
    done
done

# Sign requests
sudo ./easyrsa --batch sign-req server server
for t in ${TEAMS}; do
    sudo ./easyrsa --batch sign-req client team${t}
    sudo ./easyrsa --batch sign-req server team${t}_server
    for i in $(seq 1 ${NUM_MEMBERS}); do
	sudo ./easyrsa --batch sign-req client team${t}_${i}
    done
done

# DH params for the servers
sudo ./easyrsa --batch gen-dh
