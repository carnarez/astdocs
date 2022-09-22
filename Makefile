SHELL:=/bin/bash

test:
	@docker build --tag astdocs/test tests
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
	            astdocs/test python -m pytest --capture=no \
	                                           --color=yes \
	                                           --cov=astdocs \
	                                           --cov-report term-missing \
	                                           --override-ini="cache_dir=/tmp/pytest" \
	                                           --verbose \
	                                           --verbose
	@rm -fr $$(find . -name __pycache__)

html:
	@mkdir -p web/content/api/tests
	@cp astdocs/README.md web/content/api
	@cp tests/README.md web/content/api/tests
	@cd web/content; tree | sed 's/README/index/g;s/.md$$/.html/g'
	@docker build --tag astdocs/html web
	@rm -fr web/content/api
	@docker run --interactive \
	            --name astdocs-web \
	            --publish 8000:80 \
	            --rm \
	            --tty \
	            astdocs/html
