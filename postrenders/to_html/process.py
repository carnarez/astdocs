"""Render the output in `HTML`, including syntax highlighting and anchor links.

The html can be generated as follows:

```shell
$ python process.py astdocs.py > html/astdocs.html
```

Note the CSS for the syntax highlighting was generated using:

```shell
$ pygmentize -S default -f html -a .codehilite > html/styles-code.css
```

after `pip install`ing [`Pygments`](https://pygments.org/).
"""

import sys

import markdown as md
import minify_html as mh

import astdocs

headers = """
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="styles-body.css">
  <link rel="stylesheet" href="styles-code.css">
</head>
<body>
"""

footer = """
</body>
</html>
"""

mdwn = astdocs.render(sys.argv[1])
html = md.markdown(mdwn, extensions=["codehilite", "fenced_code", "toc"])
mini = mh.minify(f"{headers}{html}{footer}")

print(mini)
