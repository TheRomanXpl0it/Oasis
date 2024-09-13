FROM alpine:latest

RUN apk update && apk add iptables iproute2 bash ethtool tcpdump

COPY ./entry.sh /entry.sh
COPY --chown=root:root ./ctfroute.sh /usr/sbin/ctfroute
RUN chmod +x /entry.sh
RUN chmod +x /usr/sbin/ctfroute

CMD [ "/entry.sh" ]
