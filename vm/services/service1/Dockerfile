FROM python:3.10

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY src .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0", "app:create_app()"]