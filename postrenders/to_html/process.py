"""Render the output in `HTML`, including syntax highlighting and anchor links.

The `HTML` content can be generated as follows:

```shell
$ python process.py astdocs.py > html/astdocs.html
```

Note the CSS for the syntax highlighting was generated using:

```shell
$ pygmentize -S default -f html -a .codehilite > html/pygments.css
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
