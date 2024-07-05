#!/bin/bash

ip link set eth0 down
ip link set eth0 name game
ip link set game up

ip route add 10.10.0.0/24 via 10.60.200.200

find . -maxdepth 1 -mindepth 1 -type d -exec docker compose -f {}/compose.yml up -d \;

/usr/sbin/sshd -D

tail -f /dev/null
