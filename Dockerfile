FROM python:3.11-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x /usr/src/app/docker/app.sh
RUN chmod a+x /usr/src/app/docker/celery.sh