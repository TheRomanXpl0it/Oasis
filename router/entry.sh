#!/bin/sh

iptables -A FORWARD -i eth+ -j ACCEPT
iptables -t nat -A POSTROUTING -o eth+ -j MASQUERADE

tail -f /dev/null
