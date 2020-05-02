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
    ip=${ips[i++]}
    if [[ "${ip}" == "" ]]; then
	echo "IP unset for team ${t}, skipping user push"
	continue
    fi
    password=$(tr -dc _A-Z-a-z-0-9 < /dev/urandom | head -c32)
    echo "hacker:${password}" > team_confs/team${t}_password.txt
    scp team_confs/team${t}_password.txt ec2-user@${ip}:password.txt
    ssh ec2-user@${ip} './setup_users.sh'
done
