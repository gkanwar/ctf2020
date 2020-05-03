#!/bin/bash

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

mkdir -p team_confs
sudo cp /etc/openvpn/easy-rsa/pki/dh.pem team_confs
sudo cp /etc/openvpn/easy-rsa/pki/ca.crt team_confs
for t in ${TEAMS}; do
    sudo cp /etc/openvpn/easy-rsa/pki/issued/team${t}.crt team_confs
    sudo cp /etc/openvpn/easy-rsa/pki/issued/team${t}_server.crt team_confs
    sudo cp /etc/openvpn/easy-rsa/pki/private/team${t}.key team_confs
    sudo cp /etc/openvpn/easy-rsa/pki/private/team${t}_server.key team_confs
    for i in $(seq 1 ${NUM_MEMBERS}); do
	sudo cp /etc/openvpn/easy-rsa/pki/issued/team${t}_${i}.crt team_confs
	sudo cp /etc/openvpn/easy-rsa/pki/private/team${t}_${i}.key team_confs
    done
done
sudo chown -R `id -u`:`id -g` team_confs/*

if [[ "$GAMESERVER_IP" == "" ]]; then
    echo "Must set GAMESERVER_IP"
    exit 1
fi
for t in ${TEAMS}; do
    python3 build_client_config.py ${GAMESERVER_IP} team${t}
done

read -ra ips <<< "${VULNBOX_IPS}"
i=0
for t in ${TEAMS}; do
    echo "Server config team ${t}"
    python3 build_server_config.py ${t}
    ip=${ips[i++]}
    if [[ "${ip}" == "" ]]; then
	echo "IP unset for team ${t}, skipping client configs"
	continue
    fi
    for ind in $(seq ${NUM_MEMBERS}); do
	python3 build_client_config.py ${ip} team${t}_${ind}
    done
done

