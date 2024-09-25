FROM oasis-vm-base:latest

RUN systemctl disable init-vm.service
RUN rm /etc/systemd/system/init-vm.service
COPY ./init-vm.service /etc/systemd/system/init-vm.service
RUN systemctl enable init-vm.service

ARG TOKEN
ENV TOKEN=$TOKEN
RUN echo "root:${TOKEN:-root}" | chpasswd

ARG TEAM_NAME
ENV TEAM_NAME=$TEAM_NAME
RUN echo $TEAM_NAME >> /etc/teamname

ENTRYPOINT [ "/sbin/init", "--log-level=err" ]
