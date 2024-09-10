FROM cruizba/ubuntu-dind:latest

RUN apt-get update

RUN apt-get install -y \
	iproute2 vim nano tcpdump iputils-ping \
	python3-pip python3-venv screen netcat-openbsd

# SSH
RUN apt-get install -y openssh-server
RUN mkdir /var/run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
EXPOSE 22

# Services
WORKDIR /root/
COPY ./services/ /tmp/services/
COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh

ARG TOKEN
ENV TOKEN=$TOKEN
RUN echo "root:${TOKEN:-root}" | chpasswd

CMD ["/tmp/entry.sh"]
