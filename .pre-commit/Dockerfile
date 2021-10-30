FROM python:slim

ARG uid=1000

COPY requirements.txt /tmp/requirements.txt

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y git \
 && pip install --no-cache-dir -r /tmp/requirements.txt \
 && useradd -d /home/pre-commit -m -s /bin/bash -u $uid pre-commit

COPY hooks.yaml /home/pre-commit/hooks.yaml
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

USER $uid

WORKDIR /usr/src

ENTRYPOINT ["/bin/bash", "/usr/local/bin/entrypoint.sh"]
