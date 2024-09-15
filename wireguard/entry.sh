#!/bin/sh

SUBNET=$(ip a | grep -oP '((?<=)10.80.+.128\/24(?=))' | cut -d'.' -f3)

ip route add 10.10.0.0/24 via 10.80.$SUBNET.250
ip route add 10.60.0.0/16 via 10.80.$SUBNET.250
iptables -A FORWARD -s 10.80.$SUBNET.0/24 -d 10.0.0.0/8 -j ACCEPT
iptables -A FORWARD -s 10.80.$SUBNET.0/24 -j REJECT

tail -f /dev/null
