#!/bin/bash

###################################################
# THIS IS NOT A CHALLENGE, IS THE SETUP OF THE VM #
###################################################

while [[ ! $(docker ps) ]]; do
    sleep 1
done

if [[ "$1" == "prebuild" ]]; then
    find /services/ -maxdepth 1 -mindepth 1 -type d -exec docker compose -f {}/compose.yml build \;
    shutdown -h now
    exit 0
fi

mv /services/* /root/ 2> /dev/null
rm -rf /services
TEAM_ID=$(ip a | grep -oP '((?<=)10.60.+.1\/24(?=))' | cut -d'.' -f3)
# Set up network
ip link set eth0 name game
ip route add default via 10.60.$TEAM_ID.250

# Start services
find /root/ -maxdepth 1 -mindepth 1 -type d -exec docker compose -f {}/compose.yml up -d \; &> /tmp/service-init-logs
