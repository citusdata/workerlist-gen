FROM python:2.7-slim

ADD manager.py /

RUN pip install docker[tls] psycopg2

CMD [ "python", "./manager.py" ]