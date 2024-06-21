FROM ubuntu:20.04

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python3-pip
# RUN apt-get install -y socat
RUN apt-get install -y sqlite

RUN python3 -m pip install pycryptodome
RUN python3 -m pip install aiosqlite

RUN mkdir /service
WORKDIR /service
RUN mkdir data

COPY cry_async.py crypto.py init_client.sql checker.pubkey run.sh ./

RUN groupadd -g 2000 cryptogroup \
&& useradd -m -u 2001 -g cryptogroup cryptodude

RUN chown -R cryptodude /service
RUN chmod +x cry_async.py run.sh

CMD ["/service/run.sh"]
