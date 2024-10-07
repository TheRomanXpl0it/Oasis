FROM lscr.io/linuxserver/wireguard:latest

RUN ln -sf /sbin/iptables-nft /sbin/iptables

COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh

CMD [ "/tmp/entry.sh" ]
