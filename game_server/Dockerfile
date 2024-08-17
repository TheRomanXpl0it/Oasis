FROM golang:1.22

WORKDIR /app/

RUN apt-get update && \
	apt-get install -y python3-pip python3-venv \
		iproute2 iputils-ping

COPY ./checkers/requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages -r /tmp/requirements.txt

COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh

ENTRYPOINT [ "/tmp/entry.sh" ]
