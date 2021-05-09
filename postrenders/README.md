A few post-rendering examples I implemented in the past and found worth keeping.

If a `requirements.txt` is provided, jump into a clean environment, either:

```shell
$ python -m venv .venv
$ .venv/bin/pip install -U pip
$ .venv/bin/pip install --no-cache-dir -r requirements.txt
```

or even:

```shell
$ docker run --entrypoint /bin/bash -it --rm -v `pwd`:/usr/src --workdir /usr/src python:3.8-slim
> pip install --no-cache-dir -r requirements.txt
```

if you are fond of `Docker`. In this latter case keep in mind the user creating content
(might need to play around with `chown`).
