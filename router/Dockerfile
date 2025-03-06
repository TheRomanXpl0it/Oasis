FROM public.ecr.aws/docker/library/alpine:latest

RUN apk update && apk add iptables iproute2 bash ethtool tcpdump \
    traceroute netcat-openbsd socat iproute2-tc

COPY ./entry.sh /entry.sh
COPY --chown=root:root ./ctfroute.sh /usr/sbin/ctfroute
COPY ./ctfroute-handle.sh /ctfroute-handle.sh
RUN chmod +x /entry.sh
RUN chmod +x /usr/sbin/ctfroute

CMD [ "/entry.sh" ]
