***My* very opinionated way to pull and format `NumPy`-ish docstrings from `Python`
modules.** Get it via a simple:

```shell
$ pip install git+https://github.com/carnarez/astdocs@master
```

then installing itself as an `astdocs` command line tool on top of adding the `Python`
package to the `import` path, or:

```shell
$ wget https://raw.githubusercontent.com/carnarez/astdocs/master/astdocs/astdocs.py
```

for the script itself, whatever you find more appropriate. Accepts a single argument, a
**file** (*e.g.*, `Python` module) or a **directory** (in which it will recursively fish
for all `*.py` files).
