FROM cruizba/ubuntu-dind:latest

RUN apt update

RUN apt install -y \
	iproute2 vim nano tcpdump iputils-ping \
	python3-pip python3-venv screen

# SSH
RUN apt install -y openssh-server
RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
EXPOSE 22

# Netcat
COPY ./nc /usr/bin/nc
RUN chmod +x /usr/bin/nc

# Services
WORKDIR /root/
COPY ./services/ .
COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh

CMD ["/tmp/entry.sh"]
