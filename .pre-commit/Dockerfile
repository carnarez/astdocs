FROM python:3.9-slim

ARG username

RUN mkdir -p /home/$username \
 && chmod -R 777 /home/$username

COPY requirements.txt /tmp/requirements.txt

RUN apt-get update \
 && apt-get install --no-install-recommends --no-install-suggests --yes git \
 && pip install -U pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt

COPY hooks.yaml /usr/share/pre-commit/hooks.yaml
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

WORKDIR /usr/src

ENTRYPOINT ["/bin/bash", "/usr/local/bin/entrypoint.sh"]
