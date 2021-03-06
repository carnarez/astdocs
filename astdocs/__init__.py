# flake8: noqa
# isort: skip_file

"""Make all objects available at the root of the package.

Attributes
----------
TPL : string.Template
    Template to render the overall page (only governs order of objects in the output).
TPL_CLASSDEF : string.Template
    Template to render `class` objects.
TPL_FUNCTIONDEF : string.Template
    Template to render `def` objects (async or not).
TPL_MODULE : string.Template
    Template to render the module summary.
format_annotation : typing.Callable
    Format an annotation (object type or decorator).
format_docstring : typing.Callable
    Format the object docstring.
parse_class : typing.Callable
    Parse a `class` statement.
parse_function : typing.Callable
    Parse a `def` statement.
parse_import : typing.Callable
    Parse `import ... [as ...]` and `from ... import ... [as ...]` statements.
parse : typing.Callable
    Recursively traverse the nodes of the abstract syntax tree.
render_class : typing.Callable
    Render a `class` object, according to the defined `TPL_CLASSDEF` template.
render_function : typing.Callable
    Render a `def` object (function or method).
render_module : typing.Callable
    Render a module summary as a `Markdown` file.
render : typing.Callable
    Run the whole pipeline (useful wrapper function when this gets used as a module).
render_recursively : typing.Callable
    Run pipeline on each `Python` module found in a folder and its subfolders.
postrender : typing.Callable
    Apply a post-rendering function on the output of the decorated function.
"""

from .astdocs import (
    format_docstring,
    parse_annotation,
    parse_class,
    parse_function,
    parse_import,
    parse,
    render_class,
    render_function,
    render_module,
    render,
    render_recursively,
    postrender,
)

from .astdocs import (
    TPL,
    TPL_CLASSDEF,
    TPL_FUNCTIONDEF,
    TPL_MODULE,
    config,
    objects,
)
