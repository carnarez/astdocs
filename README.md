**_My_ very opinionated way to pull and format `NumPy`-ish docstrings from `Python`
modules.** Get it via a simple:

```shell
$ pip install git+https://github.com/carnarez/astdocs@master
```

then installing itself as an `astdocs` command line tool (on top of adding the `Python`
package to the `import` path), or:

```shell
$ wget https://raw.githubusercontent.com/carnarez/astdocs/master/astdocs/astdocs.py
```

for the script itself, whatever you find more
[appropriate](https://github.com/carnarez/utils/tree/master/astdocs). Accepts a single
argument, a **file** (*e.g.*, `Python` module) or a **directory** (in which it will
recursively fish for all `*.py` files, hidden folders like `.venv` excluded); see
`astdocs --help`. Due to its
[cleaner type hints](https://peps.python.org/pep-0604/) `Python` v3.10 is required
(tested up to v3.14).

This little stunt is fully
[tested](https://github.com/carnarez/astdocs/actions/workflows/test.yaml) (100%
coverage) and linted (via [`Ruff`](https://docs.astral.sh/ruff/), configured in
`pyproject.toml`):

```shell
$ make test  # or simply python -m pytest, from the root of the repository
```

See an example -documentation of this very script- of the `Markdown` output generated
via this little DIY and rendered by the GitHub engine [here](/astdocs/README.md). It
is also accessible [there](https://carnarez.github.io/astdocs/) for me to test the
[not so] new [GitHub Pages](https://pages.github.com/) service and some rendering
processing.
