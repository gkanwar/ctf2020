#!/bin/bash

sudo iptables -A FORWARD -j DROP
sudo iptables -t nat -A POSTROUTING -s 10.10.0.0/16 -d 10.10.0.0/16 -j MASQUERADE
