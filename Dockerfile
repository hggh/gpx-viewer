FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install --no-install-recommends -y \
 libpython3-dev \
 libpq-dev \
 gcc \
 virtualenv

WORKDIR /app
COPY requirements.txt /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt