#!/bin/bash

iptables-nft -o eth+ -t nat -A POSTROUTING -j MASQUERADE

# Set up network rules (if network close policy will be set to DROP)
# Here are setted the always allowed connections
iptables-nft -o eth+ -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables-nft -o eth+ -A FORWARD -s 10.10.0.0/16 -j ACCEPT
iptables-nft -o eth+ -A FORWARD -d 10.10.0.1 -j ACCEPT

for i in $(seq 0 $(($NTEAM-1))) ; do
    #traffic from team to the self-VM is allowed
    iptables-nft -o eth+ -A FORWARD -s 10.80.$i.0/24 -d 10.60.$i.1 -j ACCEPT
    #Allow traffic between team members
    iptables-nft -o eth+ -A FORWARD -s 10.80.$i.0/24 -d 10.80.$i.0/24 -j ACCEPT
done
iptables-nft -o eth+ -A FORWARD -s 10.0.0.0/8 -d 10.80.0.0/16 -j REJECT

echo "Created rules for $NTEAM teams"

if [[ "$VM_NET_LOCKED" != "n" ]]; then
    ctfroute lock
fi

rm -f /unixsk/ctfroute.sock
socat UNIX-LISTEN:/unixsk/ctfroute.sock,reuseaddr,fork EXEC:"bash /ctfroute-handle.sh" &
SERVER_PID=$!
trap "kill $SERVER_PID" EXIT
tail -f /dev/null