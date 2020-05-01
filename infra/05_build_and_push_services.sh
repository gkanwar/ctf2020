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

cd ${HOME}/ctf2020 && python3 build_service.py

read -ra ips <<< "${VULNBOX_IPS}"
i=0
for t in ${TEAMS}; do
    ip=${ips[i++]}
    if [[ "${ip}" == "" ]]; then
	echo "IP unset for team ${t}, skipping service push"
	continue
    fi
    ssh ec2-user@${ip} 'sudo rm -rf /tasks'
    ssh ec2-user@${ip} 'sudo mkdir -p /tasks/deep_thoughts'
    ssh ec2-user@${ip} 'sudo chown ec2-user:ec2-user -R /tasks'
    scp -r service_prod/* ec2-user@${ip}:/tasks/deep_thoughts
    ssh ec2-user@${ip} 'sudo chown hacker:hacker -R /tasks'
done
