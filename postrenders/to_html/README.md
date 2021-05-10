# Module `process`

Render the output in `HTML`, including syntax highlighting and anchor links.

The `HTML` content can be generated as follows:

```shell
$ python process.py astdocs.py > html/astdocs.html
```

Note the CSS for the syntax highlighting was generated using:

```shell
$ pygmentize -S default -f html -a .codehilite > html/styles-code.css
```

after `pip install`ing [`Pygments`](https://pygments.org/).
