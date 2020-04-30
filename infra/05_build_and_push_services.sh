#!/bin/bash

if [[ "$NUM_TEAMS" == "" ]]; then
    echo "Must set NUM_TEAMS"
    exit 1
fi

cd ${HOME}/ctf2020 && python3 build_service.py

read -ra ips <<< "${VULNBOX_IPS}"
for t in $(seq 0 ${NUM_TEAMS}); do
    ip=${ips[t]}
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
