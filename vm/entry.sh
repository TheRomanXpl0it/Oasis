#!/bin/bash

mv /tmp/services/* /root/

# Set up network
ip link set eth0 name game
ip route add 10.10.0.0/24 via 10.60.200.200

#Wait for docker starts
while [[ ! $(docker ps) ]]; do
    sleep 1
done

# Start sshd
/usr/sbin/sshd -D &

# Start services
find /root/ -maxdepth 1 -mindepth 1 -type d -exec docker compose -f {}/compose.yml up -d \; &> /tmp/service-init-logs

tail -f /dev/null
