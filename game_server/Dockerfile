FROM --platform=$BUILDPLATFORM docker.io/oven/bun AS frontend 
WORKDIR /app
ADD ./frontend/package.json .
ADD ./frontend/bun.lockb .
RUN bun install
COPY ./frontend/ .
RUN bun run build

FROM golang:1.22

WORKDIR /app/

RUN apt-get update && \
	apt-get install -y python3-pip python3-venv \
		iproute2 iputils-ping netcat-openbsd traceroute tcpdump ethtool iptables

COPY ./checkers/requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages -r /tmp/requirements.txt

COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh
WORKDIR /app/src/
COPY ./src/go.mod ./src/go.sum /app/src/
RUN go mod download
WORKDIR /app/src/
COPY ./src/ .
WORKDIR /app/src/
RUN go build .
WORKDIR /app/src/frontend
COPY --from=frontend /app/dist .
WORKDIR /app/src/

ENTRYPOINT [ "/tmp/entry.sh" ]
