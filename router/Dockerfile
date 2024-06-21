FROM alpine:latest

RUN apk update && \
	apk add iptables iproute2

COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh

ENTRYPOINT [ "/tmp/entry.sh" ]
