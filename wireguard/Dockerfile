FROM lscr.io/linuxserver/wireguard:latest

RUN ln -sf /sbin/iptables-nft /sbin/iptables

COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh
RUN sed -i /^DNS/d /defaults/peer.conf
RUN ln -sf $(which iptables-nft) $(which iptables)

CMD [ "/tmp/entry.sh" ]
