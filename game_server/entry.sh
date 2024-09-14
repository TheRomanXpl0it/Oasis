#!/bin/bash

ip route add default via 10.10.0.250
echo "127.0.0.1 flagid" >> /etc/hosts

go run .
