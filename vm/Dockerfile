FROM oasis-vm-base:latest

ARG TOKEN
ENV TOKEN=$TOKEN
RUN echo "root:${TOKEN:-root}" | chpasswd

ENTRYPOINT [ "/sbin/init" ]
