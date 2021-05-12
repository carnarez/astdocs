SHELL=/bin/bash

toc:
	@sed -n '/A few/,/# Snippets/p' README.md > tmp1
	@python3 with_toc.py | sed 's/^#/##/g' > tmp2
	@cat tmp? > README.md
	@rm tmp?

.venv:
	@python -m venv .venv
	@.venv/bin/pip install -U pip
	@.venv/bin/pip install --no-cache-dir git+https://github.com/carnarez/astdocs@master

linted_output: .venv
	@.venv/bin/pip install --no-cache-dir mdformat

object_graph: .venv

to_html: .venv
	@.venv/bin/pip install --no-cache-dir markdown minify-html pygments

with_toc: .venv

clean:
	-@rm -fr .venv `find . -name __pycache__`
