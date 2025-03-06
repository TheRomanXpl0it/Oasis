#!/bin/bash

# Define the traffic control parameters
if [[ -n "$RATE_NET" ]]; then
    # Get all interfaces used by default routes
    DEFAULT_IFACES=$(ip route | grep default | awk '{print $5}' | sort | uniq)

    # Loop through all network interfaces except 'lo' and default route interfaces
    for iface in $(ip -o link show | awk -F': ' '{print $2}' | grep -Ev "^lo" | cut -d'@' -f1); do

        # Only apply tc if the interface is not part of the default routes
        if ip addr show "$iface" | grep -q "inet " && ! echo "$DEFAULT_IFACES" | grep -q "$iface"; then
            echo "Applying traffic control on interface $iface..."
            tc qdisc add dev "$iface" root tbf rate $RATE_NET burst 32kbit latency 400ms
        fi
    done
fi

iptables -o eth+ -t nat -A POSTROUTING -j MASQUERADE

# Set up network rules (if network close policy will be set to DROP)
# Here are setted the always allowed connections
iptables -o eth+ -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

iptables -o eth+ -A FORWARD -s 10.10.0.0/16 -j ACCEPT
iptables -o eth+ -A FORWARD -d 10.10.0.1 -j ACCEPT

for i in $(seq 0 $(($NTEAM-1))) ; do
    #traffic from team to the self-VM is allowed
    iptables -o eth+ -A FORWARD -s 10.80.$i.0/24 -d 10.60.$i.1 -j ACCEPT
    #Allow traffic between team members
    iptables -o eth+ -A FORWARD -s 10.80.$i.0/24 -d 10.80.$i.0/24 -j ACCEPT
done
iptables -o eth+ -A FORWARD -s 10.0.0.0/8 -d 10.80.0.0/16 -j REJECT

echo "Created rules for $NTEAM teams"

if [[ "$VM_NET_LOCKED" != "n" ]]; then
    ctfroute lock
fi

rm -f /unixsk/ctfroute.sock
socat UNIX-LISTEN:/unixsk/ctfroute.sock,reuseaddr,fork EXEC:"bash /ctfroute-handle.sh" &
SERVER_PID=$!
trap "kill $SERVER_PID" EXIT
tail -f /dev/null
