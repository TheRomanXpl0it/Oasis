FROM python:3.8-slim

RUN useradd -M -s /bin/false mudarabah

RUN mkdir -p /services/mudarabah

WORKDIR /services/mudarabah

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY service/ .

USER mudarabah

CMD [ "gunicorn", "--bind", "0.0.0.0:3113", "--workers", "4", "--worker-connections", "1024", "main:app"]