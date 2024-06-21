FROM golang:1.15.6-alpine3.12 as build-env

RUN mkdir -p /app/
WORKDIR /app/

ENV GO111MODULE=on
ENV CGO_ENABLED=0

COPY . .

# cache modules
RUN go build -o service ./cmd

# minify image
FROM scratch
COPY --from=build-env /app/service /app/service
ENTRYPOINT ["/app/service"]