FROM ubuntu:22.04

RUN apt update && apt install -y socat

RUN useradd -d /home/chall/ -m -p chall -s /bin/bash chall
RUN echo "chall:chall" | chpasswd

WORKDIR /home/chall/
COPY ponn_hotel .
RUN chmod +x ponn_hotel
RUN mkdir -p cc bookings users
RUN chmod 777 -R ./
EXPOSE 1337

USER chall

CMD [ "socat", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:./ponn_hotel" ]
