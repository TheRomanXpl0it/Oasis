FROM oasis-vm-base:latest

ARG TOKEN
ENV TOKEN=$TOKEN
RUN echo "root:${TOKEN:-root}" | chpasswd

ARG TEAM_NAME
ENV TEAM_NAME=$TEAM_NAME
RUN echo $TEAM_NAME >> /etc/teamname

ENTRYPOINT [ "/sbin/init", "--log-level=err" ]
