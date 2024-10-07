#!/bin/bash

###################################################
# THIS IS NOT A CHALLENGE, IS THE SETUP OF THE VM #
###################################################

if [[ "$1" == "prebuild" ]]; then
    # Only with this for loop we can exit internally from the loop
    for path in $(find /services/ -maxdepth 1 -mindepth 1 -type d); do
        if [[ -f "$path/compose.yml" || -f "$path/compose.yaml" || -f "$path/docker-compose.yml" || -f "$path/docker-compose.yaml" ]]; then
            cd $path
            echo "Building $path"
            podman compose build
            EXITCODE=$?
            echo "Build of $path exited with $EXITCODE"
            if [[ "$EXITCODE" != 0 ]]; then
                echo "Failed to build $path"
                exit $EXITCODE
            fi
        fi
    done
    echo "Prebuild execution done"
    exit 0
fi

mv /services/* /root/ 2> /dev/null
rm -rf /services
TEAM_ID=$(ip a | grep -oP '((?<=)10.60.+.1\/24(?=))' | cut -d'.' -f3)
# Set up network
ip link set eth0 name game
ip route add default via 10.60.$TEAM_ID.250

mkdir -p /var/run/sshd
ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N ''
/usr/sbin/sshd -D &
SSDPID=$!

find /root/ -maxdepth 1 -mindepth 1 -type d -print0 | while read -d $'\0' path
do
    if [[ -f "$path/compose.yml" || -f "$path/compose.yaml" || -f "$path/docker-compose.yml" || -f "$path/docker-compose.yaml" ]]; then
        cd $path
        if [[ -f "$path/predeploy.sh" ]]; then
            echo "Executing predeploy.sh"
            bash predeploy.sh
        fi
        podman compose up -d --build
    fi
done

trap "kill $SSDPID" EXIT
tail -f /dev/null

# Pre Deploy script can be useful to run some commands before the deployment of the services
# Eg.

# #!/usr/bin/bash
# cd $(dirname "$(readlink -f $0)")
# if [[ ! -f ".env" ]]; then
#     echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
# fi

#To generate an .env file with a random SECRET_KEY different for each team

