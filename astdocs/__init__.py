"""Make all objets available at the root of the package."""

import astdocs
from astdocs import format_annotation  # noqa
from astdocs import format_docstring  # noqa
from astdocs import parse_classdef  # noqa
from astdocs import parse_functiondef  # noqa
from astdocs import parse_import  # noqa
from astdocs import parse_tree  # noqa
from astdocs import postrender  # noqa
from astdocs import render  # noqa
from astdocs import render_classdef  # noqa
from astdocs import render_functiondef  # noqa
from astdocs import render_module  # noqa
from astdocs import render_recursively  # noqa

__doc__ = astdocs.__doc__
