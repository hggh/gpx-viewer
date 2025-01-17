FROM python:3.13-slim-bookworm
EXPOSE 8000
VOLUME /app/gpxviewr/local_settings.py

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install --no-install-recommends -y \
 libpython3-dev \
 libpq-dev \
 gcc \
 virtualenv \
 git \
 libgdal32

COPY gpxviewr /app
COPY bootup.sh /bootup.sh

COPY requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

WORKDIR /app


CMD /bootup.sh
