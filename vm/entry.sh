#!/bin/bash

###################################################
# THIS IS NOT A CHALLENGE, IS THE SETUP OF THE VM #
###################################################

mv /tmp/services/* /root/ 2> /dev/null
TEAM_ID=$(ip a | grep -oP '((?<=)10.60.+.1\/24(?=))' | cut -d'.' -f3)
# Set up network
ip link set eth0 name game
ip route del default
ip route add default via 10.60.$TEAM_ID.250

# Start sshd
/usr/sbin/sshd -D &

# Start services
find /root/ -maxdepth 1 -mindepth 1 -type d -exec docker compose -f {}/compose.yml up -d \; &> /tmp/service-init-logs

tail -f /dev/null
