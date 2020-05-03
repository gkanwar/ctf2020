#!/bin/bash

if [[ "$NUM_TEAMS" == "" ]]; then
    echo "Must set NUM_TEAMS"
    exit 1
fi
if [[ "$NOP_ID" == "" ]]; then
    echo "Must set NOP_ID"
    exit 1
fi

TEAMS="${NOP_ID} $(seq 1 ${NUM_TEAMS})"

read -ra ips <<< "${VULNBOX_IPS}"
i=0
for t in ${TEAMS}; do
    echo "Installing ccd in gameserver"
    sudo sh -c "echo 'ifconfig-push 10.10.${t}.1 10.10.${t}.2' > /etc/openvpn/ccd/team${t}"
    ip=${ips[i++]}
    if [[ "${ip}" == "" ]]; then
	echo "IP unset for team ${t}, skipping config push"
	continue
    fi
    ssh ec2-user@${ip} 'mkdir -p ovpn_confs'
    scp team_confs/team${t}.conf ec2-user@${ip}:ovpn_confs/vuln_client.conf
    scp team_confs/team${t}_server.conf ec2-user@${ip}:ovpn_confs/vuln_server.conf
    ssh ec2-user@${ip} 'sudo cp ovpn_confs/vuln_client.conf /etc/openvpn/client/'
    ssh ec2-user@${ip} 'sudo cp ovpn_confs/vuln_server.conf /etc/openvpn/server/'
    ssh ec2-user@${ip} './restart_services.sh'
    ssh ec2-user@${ip} './setup_nat.sh'
done
