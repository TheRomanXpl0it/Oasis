#!/bin/sh

SUBNET=$(ip a | grep -oP '((?<=)10.80.+.128\/24(?=))' | cut -d'.' -f3)

ip route add 10.10.0.0/24 via 10.80.$SUBNET.200
ip route add 10.60.0.0/16 via 10.80.$SUBNET.200


tail -f /dev/null
