FROM --platform=$BUILDPLATFORM oven/bun as frontend 
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
		iproute2 iputils-ping

COPY ./checkers/requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages -r /tmp/requirements.txt

COPY ./entry.sh /tmp/
RUN chmod +x /tmp/entry.sh
WORKDIR /app/src/
COPY ./src/go.mod ./src/go.sum /app/src/
RUN go mod download
WORKDIR /app/src/
COPY ./src/ .
WORKDIR /app/checkers/
COPY ./checkers/ .
WORKDIR /app/src/frontend
COPY --from=frontend /app/dist .
WORKDIR /app/src/
RUN go build .

ENTRYPOINT [ "/tmp/entry.sh" ]
