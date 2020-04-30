#!/bin/bash

if [[ "$NUM_TEAMS" == "" ]]; then
    echo "Must set NUM_TEAMS"
    exit 1
fi

read -ra ips <<< "${VULNBOX_IPS}"
for t in $(seq 0 ${NUM_TEAMS}); do
    ip=${ips[t]}
    if [[ "${ip}" == "" ]]; then
	echo "IP unset for team ${t}, skipping user push"
	continue
    fi
    password=$(tr -dc _A-Z-a-z-0-9 < /dev/urandom | head -c32)
    echo "hacker:${password}" > team_confs/team${t}_password.txt
    scp team_confs/team${t}_password.txt ec2-user@${ip}:password.txt
done
