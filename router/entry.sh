#!/bin/sh

ifaces=$(ip link show | sed -n 's/.*\(eth.*\)@.*/\1/p')

for iface in $ifaces; do
	iptables -A FORWARD -i $iface -j ACCEPT
	iptables -t nat -A POSTROUTING -o $iface -j MASQUERADE
done

tail -f /dev/null
