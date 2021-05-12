FROM python:3.8-slim

ARG uid=1000

COPY requirements.txt /tmp/

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y git \
 && pip install --no-cache-dir -r /tmp/requirements.txt \
 && useradd -d /home/pre-commit -m -s /bin/bash -u $uid pre-commit

COPY entrypoint.sh /usr/local/bin/

USER $uid

WORKDIR /usr/src

ENTRYPOINT ["/bin/bash", "/usr/local/bin/entrypoint.sh"]
