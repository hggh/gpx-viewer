FROM python:3.13-slim-bookworm
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install --no-install-recommends -y \
 libpython3-dev \
 libpq-dev \
 gcc \
 virtualenv \
 git \
 libgdal32

 RUN groupadd -g 1337 dev
 RUN useradd -m -u 1337 -g dev -s /bin/bash dev
 
 CMD exec /bin/bash -c "trap : TERM INT; sleep infinity & wait"
