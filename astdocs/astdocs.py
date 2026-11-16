r"""Extract and format `Markdown` documentation from `Python` code.

_According to_ **my** _standards._

In a few more words, parse the underlying Abstract Syntax Tree (AST) description. (See
the [documentation](https://docs.python.org/3/library/ast.html) of the standard library
module with same name.) It expects a relatively clean input (demonstrated in this very
script) which forces *me* to keep *my* code somewhat correctly documented and without
fancy syntax.

My only requirement was to use the `Python` standard library **exclusively** (even the
[templating](https://docs.python.org/3/library/string.html#template-strings)) as it is
quite [overly] complete these days, and keep it as *lean* as possible. Support for
corner cases is scarse...

The simplest way to check the output of this script is to run it on itself:

```shell
$ python astdocs.py astdocs.py  # pipe it to your favourite markdown linter
```

or even:

```shell
$ python astdocs.py .  # recursively look for *.py files in the current directory
```

When processing a folder, hidden subfolders (`.git`, `.venv`, *etc.*) are skipped, as
are modules that cannot be parsed (a warning is written to `stderr`). See
`python astdocs.py --help` for a short summary of the usage.

The behaviour of this little stunt can be modified via environment variables:

* `ASTDOCS_BOUND_OBJECTS` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored/counted as negative) to add `%%%START ...` and `%%%END ...` markers
  to indicate the beginning/end of an object (useful for further styling when rendering
  in `HTML` for example). **Not to be mixed up with the `%%%BEGIN` markers** (see
  below).
* `ASTDOCS_FOLD_ARGS_AFTER` to fold long object (function/method) definitions (many
  parameters). Defaults to 88 characters, [`black`](https://github.com/psf/black)
  [recommended](https://www.youtube.com/watch?v=wf-BqAjZb8M&t=260s&ab_channel=PyCon2015)
  default.
* `ASTDOCS_SHOW_PRIVATE` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored) to show `Python` private objects (which names start with an
  underscore).
* `ASTDOCS_SPLIT_BY` taking the `m`, `mc`, `mfc` or an empty value (default, all
  rendered content in one output): split each **m**odule, **f**unction and/or **c**lass
  (by adding `%%%BEGIN ...` markers). Classes will always keep their methods. In case
  `mfc` is provided, the module will only keep its docstring, and each
  function/class/method will be marked.
* `ASTDOCS_WITH_LINENOS` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored) to show the line numbers of the object in the code source (to be
  processed later on by your favourite `Markdown` renderer). Look for the
  `%%%SOURCE ...` markers.

```shell
$ ASTDOCS_WITH_LINENOS=on python astdocs.py astdocs.py
```

or to split marked sections into separate files:

```shell
$ ASTDOCS_SPLIT_BY=mc python astdocs.py module.py | csplit -qz - '/^%%%BEGIN/' '{*}'
$ sed '1d' xx00 > module.md
$ rm xx00
$ for f in xx??; do
>   path=$(grep -m1 '^%%%BEGIN' $f | sed -r 's|%%%.* (.*)|\1|g;s|\.|/|g')
>   mkdir -p $(dirname $path)
>   sed '1d' $f > "$path.md"  # double quotes are needed
>   rm $f
> done
```

(See also the `Python` example in the docstring of the `astdocs.render_recursively()`
function.)

Each of these environment variables translates into a configuration option stored in the
`config` dictionnary of the present module. The key name is lowercased and stripped from
the `ASTDOCS_` prefix. The `TPL_*` templates are never modified: each rendering derives
its own copy (with or without the markers) from them and the configuration it is given,
such that successive calls with different configurations do not interfere.

Objects defined within conditional blocks (`if`, `try`, `with`, *etc.*) are documented
as if they were defined at the level of the block itself. Classes defined within classes
are rendered right after their parent; functions defined within functions are recorded
in `objects` but not rendered.

When handling rendering programmatically one can use helper [private] functions (if
necessary). See code and/or tests for details.

All encountered objects are stored as they are parsed. The content of the corresponding
attribute can be used by external scripts to generate a dependency graph, or simply a
Table of Contents:

```python
import astdocs

def toc(objects: dict[str, dict[str, dict[str, str]]]) -> str:
    md = ""

    for m in objects:  # each module
        anchor = m.replace(".", "")  # github
        md += f"\n- [`{m}`](#module-{anchor})"
        for t in ["functions", "classes"]:  # relevant object types
            for o in objects[m][t]:
                anchor = (m + o).replace(".", "")  # github
                md += f"\n    - [`{m}.{o}`](#{anchor})"

    return md

md = astdocs.render_recursively(".")
toc = toc(astdocs.objects)

print(f"{toc}\n\n{md}")
```

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
objects : dict[str, typing.Any]
    Nested dictionary of all relevant objects encountered while parsing the source code.

"""

import argparse
import ast
import functools
import os
import pathlib
import re
import string
import sys
import typing

TPL: string.Template = string.Template("$module\n\n$functions\n\n$classes")

TPL_CLASSDEF: string.Template = string.Template(
    "\n%%%START CLASSDEF $ancestry.$classname"
    "\n$hashtags `$ancestry.$classname`"
    "\n"
    "\n$classdocs"
    "\n"
    "\n$decoration"
    "\n"
    "\n$funcnames"
    "\n"
    "\n%%%SOURCE $path:$lineno:$endlineno"
    "\n"
    "\n$hashtags# Constructor"
    "\n"
    "\n```python"
    "\n$classname($params)"
    "\n```"
    "\n"
    "\n$constdocs"
    "\n"
    "\n$functions"
    "\n%%%END CLASSDEF $ancestry.$classname",
)

TPL_FUNCTIONDEF: string.Template = string.Template(
    "\n%%%START FUNCTIONDEF $ancestry.$funcname"
    "\n$hashtags `$ancestry.$funcname`"
    "\n"
    "\n```python"
    "\n$funcname($params)$output:"
    "\n```"
    "\n"
    "\n$funcdocs"
    "\n"
    "\n$decoration"
    "\n"
    "\n%%%SOURCE $path:$lineno:$endlineno"
    "\n%%%END FUNCTIONDEF $ancestry.$funcname",
)

TPL_MODULE: string.Template = string.Template(
    "\n%%%START MODULE $module"
    "\n# Module `$module`"
    "\n"
    "\n$docstring"
    "\n"
    "\n$funcnames"
    "\n"
    "\n$classnames"
    "\n%%%END MODULE $module",
)

# default configuration
config: dict[str, typing.Any] = {
    "bound_objects": False,
    "fold_args_after": 88,
    "show_private": False,
    "split_by": "",
    "with_linenos": False,
}

# all objects encountered; global variable (easier than passing it around)
objects: dict[str, typing.Any] = {}


def _update_configuration() -> dict[str, typing.Any]:
    """Update default configuration from environment variables.

    Returns
    -------
    : dict[str, typing.Any]
        Updated configuration.

    """
    truthy = ("1", "on", "true", "yes")

    # if requested, add markers indicating the start and end of an object definition
    config.update(
        {
            "bound_objects": (os.environ.get("ASTDOCS_BOUND_OBJECTS", "off") in truthy),
        },
    )

    # set the string length limit (black default)
    config.update(
        {"fold_args_after": int(os.environ.get("ASTDOCS_FOLD_ARGS_AFTER", "88"))},
    )

    # if requested, show private objects in the output
    config.update(
        {
            "show_private": (os.environ.get("ASTDOCS_SHOW_PRIVATE", "off") in truthy),
        },
    )

    # if requested, split things up with %%% markers
    config.update({"split_by": os.environ.get("ASTDOCS_SPLIT_BY", "")})

    # if requested, add the line numbers to the source
    config.update(
        {
            "with_linenos": (os.environ.get("ASTDOCS_WITH_LINENOS", "off") in truthy),
        },
    )

    return config


def _derive_template(kind: str, config: dict[str, typing.Any]) -> string.Template:
    """Derive a template from its `TPL_*` default, according to the given configuration.

    The default templates are left untouched: markers are added or removed on a copy
    each time this function is called. Successive renderings with different
    configurations therefore neither pile up nor lose markers.

    Parameters
    ----------
    kind : str
        Type of object the template is meant for, as written in the markers:
        `CLASSDEF`, `FUNCTIONDEF` or `MODULE`.
    config : dict[str, typing.Any]
        Configuration options used to derive the template.

    Returns
    -------
    : string.Template
        Template ready for substitution.

    """
    tpl, ident, split = {
        "CLASSDEF": (TPL_CLASSDEF, "$ancestry.$classname", "c"),
        "FUNCTIONDEF": (TPL_FUNCTIONDEF, "$ancestry.$funcname", "f"),
        "MODULE": (TPL_MODULE, "$module", "m"),
    }[kind]
    s = tpl.template

    # keep (or not) the "%%%START ..." and "%%%END ..." markers
    if not config["bound_objects"]:
        s = re.sub(rf"\n%%%[A-Z]+ {kind} {re.escape(ident)}", "", s)

    # add (or not) the "%%%BEGIN ..." marker
    if split in config["split_by"]:
        s = f"%%%BEGIN {kind} {ident}{s}"

    # keep (or not) the "%%%SOURCE ...:...:..." markers
    if not config["with_linenos"]:
        s = s.replace("\n\n%%%SOURCE $path:$lineno:$endlineno", "")

    return string.Template(s)


def _is_visible(path: str, config: dict[str, typing.Any]) -> bool:
    """Tell whether an object should be rendered, given its privacy.

    Parameters
    ----------
    path : str
        Absolute path to the object (only the last component is checked).
    config : dict[str, typing.Any]
        Configuration options (the `show_private` one is checked).

    Returns
    -------
    : bool
        Whether the object is public, or private objects are requested.

    """
    return not path.rsplit(".", 1)[-1].startswith("_") or config["show_private"]


def _summary_item(path: str, label: str, docs: str) -> str:
    """Format a bullet point linking to an object, with its first line of docstring.

    Parameters
    ----------
    path : str
        Absolute path to the object, used to build the (GitHub-style) anchor.
    label : str
        Text of the link.
    docs : str
        Formatted docstring of the object.

    Returns
    -------
    : str
        `Markdown` bullet point.

    """
    desc = docs.split("\n", maxsplit=1)[0]
    desc = f": {desc}" if desc else ""

    return f"* [`{label}`](#{path.replace('.', '').lower()}){desc}"


def format_docstring(
    node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module,
) -> str:
    r"""Format the object docstring.

    Expect some stiff `NumPy`-ish formatting (see
    [this](https://numpydoc.readthedocs.io/en/latest/example.html#example) or
    [that](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html)).
    Do try to **type** all your input parameters/returned objects. And use a linter on
    the output?

    Parameters
    ----------
    node : ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
        Source node to extract/parse docstring from.

    Returns
    -------
    : str
        The formatted docstring.

    Example
    -------
    Below the raw docstring example of what this very function is expecting as an input
    (very inceptional):

    ```text

    Parameters
    ----------
    node : ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
        Source node to extract/parse docstring from.

    Returns
    -------
    : str
        The formatted docstring.
    ```

    The code blocks are extracted and replaced by placeholders (`%%%BLOCK<n>%%%`) before
    performing the substitutions (then rolled back in). The regular expressions are then
    applied:

    * Leading hashtags (`#`) are removed from any lines starting with them as we do not
      want to conflict with the `Markdown` output.
    * Any series of words followed by a line with 3 or more hyphens is assumed to be a
      section marker (such as `Parameters`, `Returns`, `Example`, *etc.*).
    * Lines with `parameter : type` (`: type` optional) followed by a description,
      itself preceded by four spaces are formatted as input parameters.
    * Lines with `: type` (providing a type is here *mandatory*) followed by a
      description, itself preceded by four spaces are formatted as returned values.

    Keep in mind that returning **the full path** to a returned object is always
    preferable. And indeed **some of it could be inferred** from the function call
    itself, or the `return` statement. BUT this whole thing is to force *myself* to
    structure *my* docstrings correctly.

    Notes
    -----
    If the regular expression solution used here (which works for *my* needs) does not
    fulfill your standards, it is pretty easy to clobber it:

    ```python
    import ast
    import astdocs

    def my_docstring_parser(docstring: str) -> str:
        # process docstring
        return string

    def format_docstring(node: ast.*) -> str:  # simple wrapper function
        return my_docstring_parser(ast.get_docstring(node))

    astdocs.format_docstring = format_docstring

    print(astdocs.render(...))
    ```

    Known problem
    -------------
    Overall naive, stiff and *very* opinionated (again, for *my* use).

    """
    s = ast.get_docstring(node) or ""

    # extract code blocks, replace them by a placeholder; the closing "%%%" prevents the
    # placeholder of block 1 to match the beginning of block 10 when rolling back
    blocks = []
    patterns = [f"([`]{{{i}}}.*?[`]{{{i}}})" for i in range(7, 2, -1)]
    i = 0
    for p in patterns:
        for m in re.finditer(p, s, flags=re.DOTALL):
            blocks.append(m.group(1))
            s = s.replace(m.group(1), f"%%%BLOCK{i}%%%", 1)
            i += 1

    # remove trailing spaces
    s = re.sub(r" {1,}\n", r"\n", s)

    # rework any word preceded by one or more hashtag
    s = re.sub(r"\n#+\s*(.*)", r"\n**\1**", s)

    # rework any word followed by a line with 3 or more dashes
    s = re.sub(r"\n([A-Za-z ]+)\n-{3,}", r"\n**\1**\n", s)

    # rework list of arguments/descriptions (no types)
    s = re.sub(r"\n([A-Za-z0-9_]+)\n {2,}(.*)", r"\n* `\1`: \2", s)

    # rework list of arguments/types/descriptions
    s = re.sub(
        r"\n([A-Za-z0-9_]+) : ([A-Za-z0-9_\[\],\.| ]+)\n {2,}(.*)",
        r"\n* `\1` [`\2`]: \3",
        s,
    )

    # rework list of types/descriptions (return values)
    s = re.sub(r"\n: ([A-Za-z0-9_\[\],\.| ]+)\n {2,}(.*)", r"\n* [`\1`]: \2", s)

    # put the code blocks back in
    for i, b in enumerate(blocks):
        s = s.replace(f"%%%BLOCK{i}%%%", b)

    return s.strip()


def parse_annotation(a: typing.Any) -> str:  # noqa: C901, PLR0912 (one branch per node type)
    """Format an annotation (object type or decorator).

    Dive as deep as necessary within the children nodes until reaching the name of the
    module/attribute objects are annotated after; save the import path on the way.
    Recursively repeat for complicated object.

    See the code itself for some line-by-line documentation.

    Parameters
    ----------
    a : typing.Any
        The starting node to extract annotation information from.

    Returns
    -------
    : str
        The formatted annotation.

    Known problems
    --------------
    * The implementation only explicitly supports nodes I encountered in my projects.
      Any other node (`lambda` constructs, unary or arithmetic operations, *etc.*) is
      rendered via `ast.unparse()`, which might format things slightly differently
      (single quotes around strings for instance).

    """
    s = ""

    # dig deeper: module.object
    if isinstance(a, ast.Attribute):
        s = f"{parse_annotation(a.value)}.{a.attr}"

    # dig deeper: | operator (other operators are left to ast.unparse() below)
    elif isinstance(a, ast.BinOp) and isinstance(a.op, ast.BitOr):
        s = parse_annotation(a.left)
        s += " | "
        s += parse_annotation(a.right)

    # dig deeper: @decorator(including, parameter=s), with **unpacking as well
    elif isinstance(a, ast.Call):
        s = parse_annotation(a.func)
        s += "("
        s += ", ".join(
            [parse_annotation(a_) for a_ in a.args]
            + [
                f"{a_.arg}={parse_annotation(a_.value)}"
                if a_.arg is not None
                else f"**{parse_annotation(a_.value)}"
                for a_ in a.keywords
            ],
        )
        s += ")"

    # we dug deep enough and unravelled a value
    elif isinstance(a, ast.Constant):
        if isinstance(a.value, str):
            s = f'"{a.value}"'
        elif a.value is Ellipsis:
            s = "..."
        else:
            s = str(a.value)

    # dig deeper: content within a dictionnary
    elif isinstance(a, ast.Dict):
        s = "{"
        s += ", ".join(
            [
                f"{parse_annotation(k)}: {parse_annotation(v)}"
                for k, v in zip(a.keys, a.values, strict=True)
            ],
        )
        s += "}"

    # dig deeper: content within a list
    elif isinstance(a, ast.List):
        s = "["
        s += ", ".join([parse_annotation(a_) for a_ in a.elts])
        s += "]"

    # we dug deep enough and unravelled a canonical object
    elif isinstance(a, ast.Name):
        s = a.id

    # dig deeper: complex object, tuple[dict[int, float], bool, str] for instance
    elif isinstance(a, ast.Subscript):
        v = parse_annotation(a.slice)
        s = parse_annotation(a.value)
        s += "["
        s += v[1:-1] if v.startswith("(") and v.endswith(")") else v
        s += "]"

    # dig deeper: content within a set
    elif isinstance(a, ast.Set):
        s = "{"
        s += ", ".join([parse_annotation(a_) for a_ in a.elts])
        s += "}"

    # dig deeper: content within a tuple
    elif isinstance(a, ast.Tuple):
        s = "("
        s += ", ".join([parse_annotation(a_) for a_ in a.elts])
        s += ")"

    # anything else (lambda, -1, not x, ...); None (no annotation) stays an empty string
    elif isinstance(a, ast.AST):
        s = ast.unparse(a)

    return s


def parse_class(
    node: ast.ClassDef,
    module: str,
    ancestry: str,
    classes: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Parse a `class` statement.

    Parameters
    ----------
    node : ast.ClassDef
        The node to extract information from.
    module : str
        Name of the current module.
    ancestry : str
        Complete path to the object, used to identify ownership of children objects
        (functions and methods for instance).
    classes : dict[str, dict[str, str]]
        Dictionnaries of all encountered class definitions.

    Returns
    -------
    : dict[str, dict[str, str]]
        Dictionnaries of all encountered class definitions.

    """
    ap = f"{ancestry}.{node.name}"  # absolute path to the object
    lp = ap.replace(module, "", 1).lstrip(".")  # local path to the object
    objects[module]["classes"][lp] = ap  # save the object path

    # parse decorator objects
    dc = [f"`@{parse_annotation(d)}`" for d in node.decorator_list]

    # save the object details
    classes[ap] = {
        "ancestry": ancestry,
        "classname": node.name,
        "classdocs": format_docstring(node),
        "decoration": "**Decoration** via " + ", ".join(dc) + "." if dc else "",
        "endlineno": str(node.end_lineno),
        "lineno": str(node.lineno),
    }

    return classes


def _format_parameter(arg: ast.arg, val: ast.expr | None = None) -> str:
    """Parse and format a parameter.

    Parameters
    ----------
    arg : ast.arg
        The parameter node, including its potential annotation.
    val : ast.expr | None
        Default value for this parameter. Defaults to `None`.

    Returns
    -------
    : str
        Formatted parameter with potential annotation and default value.

    """
    s = arg.arg

    if arg.annotation is not None:
        s += ": "
        s += parse_annotation(arg.annotation)

    if val is not None:
        s += " = " if arg.annotation is not None else "="
        s += parse_annotation(val)

    return s


def _format_parameters(args: ast.arguments, *, skip_first: bool = False) -> list[str]:
    """Parse and format all parameters of a function signature.

    Parameters
    ----------
    args : ast.arguments
        The parameters node of the function.
    skip_first : bool
        Whether to leave the first positional parameter out (`self`, `cls`, *etc.*).
        Defaults to `False`.

    Returns
    -------
    : list[str]
        Formatted parameters, including the `/` and `*` separators.

    """
    params = []
    positional = [*args.posonlyargs, *args.args]

    # default values belong to the *last* positional parameters (posonly ones included)
    defaults = [None] * (len(positional) - len(args.defaults)) + args.defaults

    # positional-only parameters, "/", regular parameters
    for i, (arg, val) in enumerate(zip(positional, defaults, strict=True)):
        if i >= int(skip_first):
            params.append(_format_parameter(arg, val))
            if i == len(args.posonlyargs) - 1:
                params.append("/")

    # *args, or lone * to indicate the parameters below are keyword-only
    if args.vararg is not None:
        params.append(f"*{_format_parameter(args.vararg)}")
    elif args.kwonlyargs:
        params.append("*")

    # keyword-only parameters; kw_defaults contains None for those without default
    params.extend(
        _format_parameter(arg, val)
        for arg, val in zip(args.kwonlyargs, args.kw_defaults, strict=True)
    )

    # **kwargs
    if args.kwarg is not None:
        params.append(f"**{_format_parameter(args.kwarg)}")

    return params


def parse_function(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    module: str,
    ancestry: str,
    functions: dict[str, dict[str, str]],
    *,
    method: bool = False,
) -> dict[str, dict]:
    """Parse a `def` statement.

    Parameters
    ----------
    node : ast.AsyncFunctionDef | ast.FunctionDef
        The node to extract information from.
    module : str
        Name of the current module.
    ancestry : str
        Complete path to the object, used to identify ownership of children objects
        (functions and methods for instance).
    functions : dict[str, dict[str, str]]
        Dictionnaries of all encountered function definitions.
    method : bool
        Whether the function is defined within a class. If so (and unless decorated
        with `@staticmethod`) its first parameter (`self`, `cls`, *etc.*) is left out.
        Defaults to `False`.

    Returns
    -------
    : dict[str, dict]
        Dictionnaries of all encountered function definitions.

    Notes
    -----
    Parameters are rendered in the order of the signature: positional-only ones
    (followed by a `/`), regular ones, `*args` (or a lone `*` if keyword-only parameters
    follow), keyword-only ones and `**kwargs`. Default values are formatted following
    [PEP 8](https://peps.python.org/pep-0008/#other-recommendations): `a: int = 0` but
    `a=0`.

    """
    ap = f"{ancestry}.{node.name}"  # absolute path to the object
    lp = ap.replace(module, "", 1).lstrip(".")  # local path to the object
    objects[module]["functions"][lp] = ap  # save the object path

    # parse decorator objects
    ds = [parse_annotation(d) for d in node.decorator_list]
    dc = [f"`@{d}`" for d in ds]

    # parse/format parameters; leave the instance/class out of method signatures
    params = _format_parameters(
        node.args,
        skip_first=method and "staticmethod" not in ds,
    )

    # output
    output = f" -> {parse_annotation(node.returns)}" if node.returns is not None else ""

    # add line breaks if the function call is long (pre-render this latter first, no way
    # around it)
    if len(f"{node.name}({', '.join(params)}){output}") > config["fold_args_after"]:
        params = [f"\n    {p}" for p in params]
        suffix = ",\n"
    else:
        suffix = ""

    # save the object details
    functions[ap] = {
        "ancestry": ancestry,
        "params": ("," if suffix else ", ").join(params) + suffix,
        "decoration": ("**Decoration** via " + ", ".join(dc) + ".") if dc else "",
        "endlineno": str(node.end_lineno),
        "funcdocs": format_docstring(node),
        "funcname": node.name,
        "lineno": str(node.lineno),
        "output": output,
    }

    return functions


def parse_import(
    node: ast.Import | ast.ImportFrom,
    module: str,
    ancestry: str,
    imports: dict[str, str],
) -> dict[str, str]:
    """Parse `import ... [as ...]` and `from ... import ... [as ...]` statements.

    The content built by this function is currently *not* rendered. This latter is kept
    in case all the objects (and aliases) accessible within a module is required for a
    post-processing or some later [smart and exciting] implementations.

    Parameters
    ----------
    node : ast.Import | ast.ImportFrom
        The node to extract information from.
    module : str
        Name of the current module.
    ancestry : str
        Complete path to the object, used to identify ownership of children objects
        (functions and methods for instance).
    imports : dict[str, str]
        Dictionnaries of parsed imports.

    Returns
    -------
    : dict[str, str]
        Dictionnaries of all encountered imports. Untouched for now: imports are only
        recorded in `objects`.

    """
    if isinstance(node, ast.Import):
        for n in node.names:
            abspath = f"{ancestry}.{n.name}"
            locpath = n.asname or n.name

            # save the object
            objects[module]["imports"][locpath] = abspath

    if isinstance(node, ast.ImportFrom):
        m = f"{node.module}." if node.module is not None else ""
        v = node.level + 1 if node.level > 0 else 0
        for n in node.names:
            abspath = f"{ancestry}.{'.' * v}{m}{n.name}"
            locpath = n.asname or n.name

            # save the object; with support for heresy like "from .. import *" (who does
            # that seriously)
            objects[module]["imports"][locpath] = abspath

    return imports


def _statements(node: ast.AST) -> list[ast.stmt]:
    """List the statements directly nested within a node.

    Parameters
    ----------
    node : ast.AST
        Any node; compound statements (`if`, `try`, `with`, `match`, loops, *etc.*) and
        definitions (`class`, `def`, module) have nested statements.

    Returns
    -------
    : list[ast.stmt]
        All nested statements, in order (all branches included).

    """
    stmts = []

    for field in ("body", "orelse", "finalbody"):
        stmts.extend(getattr(node, field, []))
    for h in getattr(node, "handlers", []):  # try ... except ...
        stmts.extend(h.body)
    for c in getattr(node, "cases", []):  # match ... case ...
        stmts.extend(c.body)

    return stmts


def parse(  # noqa: PLR0913, PLR0917 (signature kept for backwards compatibility)
    node: typing.Any,
    module: str,
    ancestry: str = "",
    classes: dict[str, dict[str, str]] | None = None,
    functions: dict[str, dict[str, str]] | None = None,
    imports: dict[str, str] | None = None,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, str]]:
    """Recursively traverse the nodes of the abstract syntax tree.

    The present function calls the formatting function corresponding to the node name
    (if supported) to parse/format it. Compound statements (`if`, `try`, *etc.*) are
    traversed as well, their content being attached to the current ancestry.

    Parameters
    ----------
    node : typing.Any
        Any type of node to extract information from.
    module : str
        Name of the current module.
    ancestry : str
        Complete path to the object, used to identify ownership of children objects
        (functions and methods for instance).
    classes : dict[str, dict[str, str]] | None
        Dictionnaries of parsed class definitions. Defaults to `None`.
    functions : dict[str, dict[str, str]] | None
        Dictionnaries of parsed function definitions. Defaults to `None`.
    imports : dict[str, str] | None
        Dictionnaries of parsed imports. Defaults to a `None`.

    Returns
    -------
    : dict[str, dict[str, str]]
        Dictionnaries of all encountered class definitions.
    : dict[str, dict[str, str]]
        Dictionnaries of all encountered function definitions.
    : dict[str, str]
        Dictionnaries of all encountered imports.

    """
    classes = {} if classes is None else classes
    functions = {} if functions is None else functions
    imports = {} if imports is None else imports

    for n in _statements(node):
        # call the parser for each supported node type, and traverse its children
        if isinstance(n, ast.ClassDef):
            classes = parse_class(n, module, ancestry, classes)
            parse(n, module, f"{ancestry}.{n.name}", classes, functions, imports)

        elif isinstance(n, ast.AsyncFunctionDef | ast.FunctionDef):
            functions = parse_function(
                n,
                module,
                ancestry,
                functions,
                method=ancestry in classes,
            )
            parse(n, module, f"{ancestry}.{n.name}", classes, functions, imports)

        elif isinstance(n, ast.Import | ast.ImportFrom):
            imports = parse_import(n, module, ancestry, imports)

        # compound statement (or not interested, nothing nested)
        else:
            parse(n, module, ancestry, classes, functions, imports)

    return classes, functions, imports


def render_class(
    filepath: str,
    name: str,
    classes: dict[str, dict[str, str]],
    functions: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
) -> str:
    """Render a `class` object, according to the defined `TPL_CLASSDEF` template.

    Only the methods directly defined within the class are rendered. Classes defined
    within the class are rendered (recursively) right after it.

    Parameters
    ----------
    filepath : str
        Path to the module (file) defining the object.
    name : str
        The name (full path including all ancestors) of the object to render.
    classes : dict[str, dict[str, str]]
        Dictionnaries of all encountered class definitions.
    functions : dict[str, dict[str, str]]
        Dictionnaries of all encountered function definitions.
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    : str
        `Markdown`-formatted description of the class object (and nested classes).

    """
    ht = "#" if "c" in config["split_by"] else "###"

    # select the methods defined directly within the class (not within nested classes
    # or within other methods)
    fs = [f for f in functions if f.rsplit(".", 1)[0] == name]

    # fetch the content of __init__
    n = f"{name}.__init__"
    if n in fs:
        fs.remove(n)
        details = functions[n]
        params = details["params"]
        docstring = details["funcdocs"]
        beglineno = details["lineno"]
        endlineno = details["endlineno"]
        if config["with_linenos"]:
            docstring += f"\n\n%%%SOURCE {filepath}:{beglineno}:{endlineno}"
    else:
        params = ""
        docstring = ""

    # keep the public methods only (unless requested otherwise)
    fs = [f for f in fs if _is_visible(f, config)]

    # methods rendered, one level below the class
    fsr = []
    for f in fs:
        functions[f].update({"hashtags": f"{ht}##"})
        fsr.append(render_function(filepath, f, functions, config))

    # methods bullet list
    fsl = [
        _summary_item(f, f"{f.rsplit('.', 1)[-1]}()", functions[f]["funcdocs"])
        for f in fs
    ]

    # update the description of the object
    classes[name].update(
        {
            "params": params,
            "constdocs": docstring,
            "functions": (ht + "# Methods\n\n" + "\n\n".join(fsr)) if fsr else "",
            "funcnames": ("**Methods**\n\n" + "\n".join(fsl)) if fsl else "",
            "hashtags": ht,
            "path": filepath,
        },
    )

    rendered = _derive_template("CLASSDEF", config).substitute(classes[name]).strip()

    # nested classes, rendered after their parent
    cs = [
        render_class(filepath, c, classes, functions, config)
        for c in classes
        if c.rsplit(".", 1)[0] == name and _is_visible(c, config)
    ]

    return "\n\n".join([rendered, *cs])


def render_function(
    filepath: str,
    name: str,
    functions: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
) -> str:
    """Render a `def` object (function or method).

    Follow the defined `TPL_FUNCTIONDEF` template.

    Parameters
    ----------
    filepath : str
        Path to the module (file) defining the object.
    name : str
        The name (full path including all ancestors) of the object to render.
    functions : dict[str, dict[str, str]]
        Dictionnaries of all encountered function definitions.
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    : str
        `Markdown`-formatted description of the function/method object.

    """
    # update the description of the object; methods already got their heading level
    # from render_class()
    functions[name].update({"path": filepath})
    functions[name].setdefault("hashtags", "#" if "f" in config["split_by"] else "###")

    return _derive_template("FUNCTIONDEF", config).substitute(functions[name]).strip()


def render_module(
    name: str,
    docstring: str,
    classes: dict[str, dict[str, str]],
    functions: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
) -> str:
    """Render a module summary as a `Markdown` file.

    Follow the defined `TPL_MODULE` template.

    Parameters
    ----------
    name : str
        Name of the module being parsed.
    docstring : str
        The docstring of the module itself, if present (defaults to an empty string).
    classes : dict[str, dict[str, str]]
        Dictionnaries of all encountered class definitions.
    functions : dict[str, dict[str, str]]
        Dictionnaries of all encountered function definitions.
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    : str
        `Markdown`-formatted description of the whole module.

    """
    # self-standing functions bullet list
    fs = [
        _summary_item(f, f"{f.rsplit('.', 1)[-1]}()", functions[f]["funcdocs"])
        for f in functions
        if f.count(".") == name.count(".") + 1 and _is_visible(f, config)
    ]

    # classes bullet list
    cs = [
        _summary_item(c, c.rsplit(".", 1)[-1], classes[c]["classdocs"])
        for c in classes
        if c.count(".") == name.count(".") + 1 and _is_visible(c, config)
    ]

    sub = {
        "classnames": "**Classes**\n\n" + "\n".join(cs) if cs else "",
        "docstring": docstring,
        "funcnames": "**Functions**\n\n" + "\n".join(fs) if fs else "",
        "module": name,
    }

    # clean up the unwanted
    if "c" in config["split_by"]:
        sub["classnames"] = ""
    if "f" in config["split_by"]:
        sub["funcnames"] = ""

    return _derive_template("MODULE", config).substitute(sub).strip()


def _module_name(filepath: str) -> str:
    """Derive the name of a module from the path to its file.

    Parameters
    ----------
    filepath : str
        Path to the module (file); relative or absolute.

    Returns
    -------
    : str
        Dotted name of the module, *e.g.*, `package.module` for `package/module.py` or
        `package` for `package/__init__.py`. The name of the current directory is used
        for a `__init__.py` file at its root.

    """
    p = pathlib.PurePath(filepath).with_suffix("")
    parts = [x for x in p.parts if x not in (p.anchor, "..")]

    if parts and parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts) or pathlib.Path.cwd().name


def render(
    filepath: str = "",
    remove_from_path: str = "",
    code: str = "",
    module: str = "",
    config: dict[str, typing.Any] = config,
) -> str:
    """Run the whole pipeline (useful wrapper function when this gets used as a module).

    Parameters
    ----------
    filepath : str
        The path to the module to process. Defaults to empty string.
    remove_from_path : str
        Part of the path to be removed. If one is rendering the content of a file buried
        deep down in a complicated folder tree *but* does not want this to appear in the
        ancestry of the module. The file itself is still read from `filepath`; the
        shortened path is used for the module name and the `%%%SOURCE` markers. Defaults
        to empty string.
    code : str
        Code to process; useful when used as a module. If both `filepath` and `code` are
        provided the latter will be ignored. Defaults to empty string.
    module : str
        Name of the current module. Defaults to empty string.
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    : str
        `Markdown`-formatted content.

    """
    if len(filepath):
        # traverse and parse the ast
        code = pathlib.Path(filepath).read_text(encoding="utf-8")
        n = ast.parse(code, filename=filepath)

        # clean up module name
        if remove_from_path:
            filepath = filepath.replace(remove_from_path, "")
        module = _module_name(filepath)

    elif len(code) and len(module):
        filepath = f"{module}.py"
        n = ast.parse(code)

    else:
        return "Nothing to do."  # user provided nOthINg

    # all objects encountered over a whole run are kept track of
    objects[module] = {"classes": {}, "functions": {}, "imports": {}}

    # parse it all
    classes, functions, _ = parse(n, module, module, {}, {}, {})

    # render the functions at the root of the module
    fs = [
        render_function(filepath, f, functions, config)
        for f in functions
        if f.count(".") == module.count(".") + 1 and _is_visible(f, config)
    ]

    # render the classes at the root of the module
    cs = [
        render_class(filepath, c, classes, functions, config)
        for c in classes
        if c.count(".") == module.count(".") + 1 and _is_visible(c, config)
    ]

    # render each section according to provided options
    sub = {
        "classes": "\n\n".join(
            [
                "## Classes" if "c" not in config["split_by"] and cs else "",
                "\n\n".join(cs) if cs else "",
            ],
        ),
        "functions": "\n\n".join(
            [
                "## Functions" if "f" not in config["split_by"] and fs else "",
                "\n\n".join(fs) if fs else "",
            ],
        ),
        "module": render_module(
            module,
            format_docstring(n),
            classes,
            functions,
            config,
        ),
    }

    s = TPL.substitute(sub).strip()

    # cleanup (extra line breaks)
    return re.sub(r"\n{3,}", "\n\n", s)


def render_recursively(
    path: str,
    remove_from_path: str = "",
    config: dict[str, typing.Any] = config,
) -> str:
    r"""Run pipeline on each `Python` module found in a folder and its subfolders.

    Hidden files and folders (starting with a dot, like `.git` or `.venv`) are skipped.
    Modules that cannot be parsed (`SyntaxError`) are skipped as well, with a warning
    written to `stderr`.

    Parameters
    ----------
    path : str
        The path to the folder to process.
    remove_from_path : str
        Part of the path to be removed.
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    : str
        `Markdown`-formatted content for all `Python` modules within the path.

    Example
    -------
    Write each module/class/function to its own file (the configuration needs to define
    the `split_by` option, see the documentation of the module):

    ```python
    import pathlib
    import astdocs

    config = astdocs.config.copy()
    config.update({"split_by": "mc"})

    outdir = pathlib.Path("docs")
    output = None

    for line in astdocs.render_recursively(..., config=config).split("\n"):
        if line.startswith("%%%BEGIN"):
            if output is not None:
                output.close()
            path = outdir.joinpath(*line.split()[2].split(".")).with_suffix(".md")
            path.parent.mkdir(parents=True, exist_ok=True)
            output = path.open("w")
        elif output is not None:
            output.write(f"{line}\n")

    if output is not None:
        output.close()
    ```

    """
    ms = []
    root = pathlib.Path(path)

    # render each module
    for filepath in sorted(root.glob("**/*.py")):
        if any(p.startswith(".") for p in filepath.relative_to(root).parts):
            continue

        name = filepath.name
        if not name.startswith("_") or config["show_private"] or name == "__init__.py":
            try:
                ms.append(
                    render(
                        filepath=str(filepath),
                        remove_from_path=remove_from_path,
                        config=config,
                    ),
                )
            except SyntaxError as e:
                sys.stderr.write(f"Skipping {filepath}: {e}\n")

    return "\n\n".join(ms)


def postrender(
    func: typing.Callable[[str], str],
) -> typing.Callable[[typing.Callable[..., str]], typing.Callable[..., str]]:
    r"""Apply a post-rendering function on the output of the decorated function.

    This can be used to streamline the linting of the output, or immediately convert to
    `HTML` for instance.

    Parameters
    ----------
    func : typing.Callable[[str], str]
        The function to apply; should take a `str` as lone input, the `Markdown` to
        process.

    Returns
    -------
    : typing.Callable[[typing.Callable[..., str]], typing.Callable[..., str]]
        Decorator returning the processed output of the decorated (rendering) function.

    Example
    -------
    Some general usage:

    ```python
    import astdocs

    def extend_that(md: str) -> str:
        # process markdown
        return string

    def apply_this(md: str) -> str:
        # process markdown
        return string

    @astdocs.postrender(extend_that)
    @astdocs.postrender(apply_this)
    def render(filepath: str) -> str:  # simple wrapper function
        return astdocs.render(filepath)

    print(render(...))
    ```

    or more concrete snippets, for instance lint the output immediately:

    ```python
    import astdocs
    import mdformat

    def lint(md: str) -> str:
        return mdformat.text(md)

    @astdocs.postrender(lint)
    def render(filepath: str) -> str:
        return astdocs.render(filepath)

    print(render(...))
    ```

    and replace the `%%%SOURCE ...` markers by `<details>` HTML tags including the code
    of each object:

    ````python
    import astdocs
    import re

    def extract_snippet(md: str) -> str:
        for m in re.finditer(r"^%%%SOURCE (.*):([0-9]+):([0-9]+)$", md, flags=re.M):
            fp, start, end = m.groups()  # path to module, first/last line of snippet
            with open(fp) as f:
                snippet = "".join(f.readlines()[int(start) - 1 : int(end)])
            md = md.replace(
                m.group(0),
                "<details><summary>Source</summary>\n\n"
                f"```python\n{snippet}```\n\n</details>",
            )
        return md

    @astdocs.postrender(extract_snippet)
    def render(filepath: str) -> str:
        config = astdocs.config.copy()
        config.update({"with_linenos": True})
        return astdocs.render(filepath, config=config)

    print(render(...))
    ````

    """

    def decorator(f: typing.Callable[..., str]) -> typing.Callable[..., str]:
        @functools.wraps(f)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> str:
            return func(f(*args, **kwargs))

        return wrapper

    return decorator


def cli(argv: list[str] | None = None) -> None:
    """Process CLI calls.

    Parameters
    ----------
    argv : list[str] | None
        Command line arguments (without the program name). Defaults to `None`, reading
        them from `sys.argv`.

    """
    parser = argparse.ArgumentParser(
        prog="astdocs",
        description="Extract and format Markdown documentation from Python code.",
        epilog=(
            "Behaviour can be modified via the ASTDOCS_BOUND_OBJECTS, "
            "ASTDOCS_FOLD_ARGS_AFTER, ASTDOCS_SHOW_PRIVATE, ASTDOCS_SPLIT_BY and "
            "ASTDOCS_WITH_LINENOS environment variables."
        ),
    )
    parser.add_argument(
        "path",
        help="Python module (file), or folder to recursively look for modules in.",
    )
    path = parser.parse_args(argv).path

    if not pathlib.Path(path).exists():
        parser.error(f"no such file or directory: {path}")

    config = _update_configuration()

    if pathlib.Path(path).is_dir():
        md = render_recursively(path, config=config)
    else:
        md = render(filepath=path, config=config)

    sys.stdout.write(f"{md}\n")


if __name__ == "__main__":  # pragma: no cover (run via subprocess in tests)
    cli()
