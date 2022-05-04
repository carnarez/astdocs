FLAGS=--rm \
      --tty \
      --user "$$(id -u)":"$$(id -g)" \
      --volume /etc/group:/etc/group:ro \
      --volume /etc/passwd:/etc/passwd:ro \
      --volume /etc/shadow:/etc/shadow:ro \
      --volume "$(PWD)/astdocs":/usr/src/astdocs \
      --volume "$(PWD)/tests":/usr/src/tests \
      --workdir /usr/src

build:
	@docker build --tag astdocs .

env: build
	@docker run --entrypoint /bin/bash --interactive --name astdocs $(FLAGS) astdocs

test: build
	@docker run $(FLAGS) --env COLUMNS=$(COLUMNS) astdocs \
	    python -m pytest --capture=no \
	                     --color=yes \
	                     --cov=astdocs \
	                     --cov-report term-missing \
	                     --override-ini="cache_dir=/tmp/pytest" \
	                     --verbose \
	                     --verbose

clean:
	@rm -fr $$(find . -name __pycache__)
	#@docker rmi --force astdocs:latest
