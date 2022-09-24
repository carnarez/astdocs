SHELL:=/bin/bash

clean:
	@rm -fr $$(find . -name __pycache__)

serve:
	@cp astdocs/README.md web/index.md
	@docker build --tag astdocs/web web
	@rm -fr web/index.md
	@docker run --interactive \
	            --name astdocs-web \
	            --publish 8000:80 \
	            --rm \
	            --tty \
	            astdocs/web

tests:
	@docker build --tag astdocs/tests tests
	@docker run --env COLUMNS=$(COLUMNS) \
	            --rm \
	            --tty \
	            --user "$$(id -u)":"$$(id -g)" \
	            --volume /etc/group:/etc/group:ro \
	            --volume /etc/passwd:/etc/passwd:ro \
	            --volume /etc/shadow:/etc/shadow:ro \
	            --volume "$(PWD)/astdocs":/usr/src/astdocs \
	            --volume "$(PWD)/tests":/usr/src/tests \
	            --workdir /usr/src \
	            astdocs/tests python -m pytest --capture=no \
	                                           --color=yes \
	                                           --cov=astdocs \
	                                           --cov-report term-missing \
	                                           --override-ini="cache_dir=/tmp/pytest" \
	                                           --verbose \
	                                           --verbose
