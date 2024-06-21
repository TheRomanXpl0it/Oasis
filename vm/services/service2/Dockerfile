FROM ubuntu:20.04

RUN apt update \
    && apt install -y python3 python3-dev socat python3-pip gcc g++ make libffi-dev

RUN pip3 install pycryptodome
RUN pip3 install rich

ADD app /service/

WORKDIR /service/

RUN chmod +x main.py

ENTRYPOINT socat -d TCP-LISTEN:3000,reuseaddr,fork EXEC:'timeout -k 5 30 python3 -u main.py'