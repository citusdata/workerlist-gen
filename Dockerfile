FROM python:2.7

ADD manager.py /

RUN pip install docker psycopg2

CMD [ "python", "./manager.py"]
