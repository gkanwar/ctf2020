#!/bin/bash

sudo iptables -I FORWARD 1 -i tun0 -o tun0 -j ACCEPT
