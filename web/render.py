"""Script to render Markdown to HTML."""

import os
import re
import sys
import typing

from jinja2 import BaseLoader, Environment, Template
from markdown import markdown
from markdown.extensions import Extension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown_astdocs import AstdocsExtension
from markdown_img import ImgExtension
from markdown_insert import InsertExtension
from markdown_script import ScriptExtension
from pymdownx.caret import InsertSupExtension
from pymdownx.emoji import EmojiExtension, gemoji
from pymdownx.highlight import HighlightExtension
from pymdownx.superfences import SuperFencesCodeExtension
from pymdownx.tilde import DeleteSubExtension

# check extension respective documentations for configuration
exts: list[Extension] = [
    AstdocsExtension(),
    DeleteSubExtension(),
    EmojiExtension(emoji_index=gemoji),
    FootnoteExtension(BACKLINK_TEXT=""),
    HighlightExtension(use_pygments=False),
    ImgExtension(),
    InsertExtension(parent_path=os.path.dirname(os.path.realpath(sys.argv[1]))),
    InsertSupExtension(),
    MarkdownInHtmlExtension(),
    ScriptExtension(),
    SuperFencesCodeExtension(),
    TableExtension(),
    TocExtension(),
]

# jinja2 template
jenv: Environment = Environment(loader=BaseLoader())
try:
    tmpl: Template = jenv.from_string(open(sys.argv[2]).read())
except IndexError:
    tmpl = jenv.from_string(open("template.html").read())

# raw markdown content
path: str = "/".join(sys.argv[1].lstrip("./").split("/")[:-1])
with open(sys.argv[1]) as f:
    text: str = f.read().strip()

# process: convert the markdown
html: str = markdown(text, extensions=exts)

# check for the presence of code and/or equations
pre = True if '<pre class="highlight">' in html else False
eqs = True if re.search(r"\$.*\$", html, flags=re.DOTALL) else False  # false positives

# render template/output to stdout and log to stderr
sys.stdout.write(tmpl.render(path=path, content=html, highlight=pre, katex=eqs))
sys.stderr.write(f'{sys.argv[1].lstrip("./")}\n')
