FROM oasis-vm-base:latest

USER root
WORKDIR /root

ARG TOKEN
ENV TOKEN=$TOKEN
RUN echo "root:${TOKEN:-root}" | chpasswd

CMD [ "/sbin/init", "entry" ]
