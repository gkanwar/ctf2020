#!/bin/bash

if [[ "$NUM_TEAMS" == "" ]]; then
    echo "Must set NUM_TEAMS"
    exit 1
fi
if [[ "$NUM_MEMBERS" == "" ]]; then
    echo "Must set NUM_MEMBERS"
    exit 1
fi

cd team_confs
for t in $(seq 1 ${NUM_TEAMS}); do
    (
	echo "team${t}_password.txt"
	for i in $(seq 1 ${NUM_MEMBERS}); do
	    echo "team${t}_${i}.conf"
	done
    ) | tar cvzf team${t}.tgz -T -
done
