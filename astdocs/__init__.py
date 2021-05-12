# flake8: noqa
# isort: skip_file

"""Make all objects available at the root of the package."""

from .astdocs import (
    format_annotation,
    format_docstring,
    parse_classdef,
    parse_functiondef,
    parse_import,
    parse_tree,
    render_classdef,
    render_functiondef,
    render_module,
    render,
    render_recursively,
    postrender,
)

from .astdocs import TPL, TPL_CLASSDEF, TPL_FUNCTIONDEF, TPL_MODULE

from .astdocs import _classdefs, _funcdefs, _module, objects
