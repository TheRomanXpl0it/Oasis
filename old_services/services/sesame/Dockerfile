FROM ubuntu:18.04

RUN set -eux; \
	groupadd -r sesame --gid=999; \
	useradd -r -g sesame --uid=999 --home-dir=/app --shell=/bin/bash sesame;

COPY bin/sesame /app/
COPY bin/run.sh /app/

WORKDIR /app

CMD ["/app/run.sh"]
