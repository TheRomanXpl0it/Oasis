#!/bin/bash

#------ AVOID NETWORK SPOOFING IP ADDRESSES ------
# ADDED TO AVOID PROBLEMS WITH NET_RAW CAPABILITY IN THE VM (Needed for capture packets)

# Get all interfaces associated with the default routes
default_ifaces=$(ip route | grep default | awk '{print $5}' | sort | uniq)

# Get all network interfaces that have an assigned IPv4 address
interfaces=$(ip -4 -o addr show | awk '{print $2}')

# Loop through each interface and apply iptables rules, excluding the default route interfaces
for iface in $interfaces; do
  # Skip the interface if it's in the list of default route interfaces
  if echo "$default_ifaces" | grep -qw "$iface"; then
    echo "Skipping default route interface: $iface"
    continue
  fi

  # Get the subnet of the interface (e.g., 10.10.0.0/24)
  subnet=$(ip -4 -o addr show "$iface" | awk '{print $4}')
  
  # If the interface has an IP address, add the iptables rule
  if [[ -n "$subnet" ]]; then
    echo "Adding iptables rule for interface $iface with subnet $subnet"
    
    # Drop all packets not from the same subnet
    iptables -t mangle -A PREROUTING -i "$iface" ! -s "$subnet" -j DROP
  fi
done

echo "All rules added successfully, excluding default route interfaces."

#------ [END] AVOID NETWORK SPOOFING IP ADDRESSES ------


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
