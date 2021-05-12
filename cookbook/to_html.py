"""Render the output in `HTML`.

Includes syntax highlighting (and code blocks), anchor links, minified `HTML` output.

Requirements
------------
* [`markdown`](https://github.com/Python-Markdown/markdown)
* [`minify-html`](https://github.com/wilsonzlin/minify-html)
* [`pygments`](https://pygments.org/)

Notes
-----
The CSS for the syntax highlighting can be generated using:

```shell
$ pygmentize -S default -f html -a .codehilite > html/pygments.css
```

check the list of available styles with `pygmentize -L`.
"""

import sys

import markdown as md
import minify_html as mh

import astdocs

headers = """
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="style.css">
  <link rel="stylesheet" href="pygments.css">
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
