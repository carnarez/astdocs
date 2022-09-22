FLAGS=--rm \
      --tty \
      --user "$$(id -u)":"$$(id -g)" \
      --volume /etc/group:/etc/group:ro \
      --volume /etc/passwd:/etc/passwd:ro \
      --volume /etc/shadow:/etc/shadow:ro \
      --volume "$(PWD)/astdocs":/usr/src/astdocs \
      --volume "$(PWD)/tests":/usr/src/tests \
      --workdir /usr/src

.PHONY: tests
tests:
	@docker build --tag astdocs/tests tests
	@docker run $(FLAGS) --env COLUMNS=$(COLUMNS) astdocs/tests \
	    python -m pytest --capture=no \
	                     --color=yes \
	                     --cov=astdocs \
	                     --cov-report term-missing \
	                     --override-ini="cache_dir=/tmp/pytest" \
	                     --verbose \
	                     --verbose
	@rm -fr $$(find . -name __pycache__)
