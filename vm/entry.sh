#!/bin/bash

###################################################
# THIS IS NOT A CHALLENGE, IS THE SETUP OF THE VM #
###################################################

mv /tmp/services/* /root/
TEAM_ID=$(ip a | grep -oP '((?<=)10.60.+.1\/24(?=))' | cut -d'.' -f3)
# Set up network
ip link set eth0 name game
ip route add 10.10.0.0/24 via 10.60.$TEAM_ID.250
ip route add 10.80.$TEAM_ID.0/24 via 10.60.$TEAM_ID.250

for i in $(seq 0 $(($NTEAM-1))) ; do
    if [[ "$i" != "$TEAM_ID" ]]; then
        ip route add 10.60.$i.0/24 via 10.60.$TEAM_ID.250
    fi
done

#Wait for docker starts
while [[ ! $(docker ps) ]]; do
    sleep 1
done

# Start sshd
/usr/sbin/sshd -D &

# Start services
find /root/ -maxdepth 1 -mindepth 1 -type d -exec docker compose -f {}/compose.yml up -d \; &> /tmp/service-init-logs

tail -f /dev/null
