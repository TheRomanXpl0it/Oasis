#!/bin/bash

ip route add 10.60.0.0/16 via 10.10.0.200

echo "127.0.0.1 flagid" >> /etc/hosts

tail -f /dev/null
