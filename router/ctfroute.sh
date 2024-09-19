#!/bin/bash

if [[ "$1" == "lock" ]]; then
    iptables -o eth+ -A FORWARD -d 10.0.0.0/8 -j REJECT && echo "Network locked!"
elif [[ "$1" == "unlock" ]]; then
    iptables -o eth+ -D FORWARD -d 10.0.0.0/8 -j REJECT && echo "Network unlocked! Game starts now!"
else
    echo "Usage: $0 [lock|unlock]"
    exit 1
fi


