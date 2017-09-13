FROM python:3

ADD manager.py /

RUN pip install docker psycopg2

CMD [ "python", "./manager.py"]
