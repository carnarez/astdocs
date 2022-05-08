r"""Extract and format `Markdown` documentation from `Python` code.

> **According to **my** standards.**

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
the `ASTDOCS_` prefix.

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

import ast
import glob
import itertools
import os
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
    "\n%%%END CLASSDEF $ancestry.$classname"
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
    "\n%%%END FUNCTIONDEF $ancestry.$funcname"
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
    "\n%%%END MODULE $module"
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
            "bound_objects": (
                True
                if os.environ.get("ASTDOCS_BOUND_OBJECTS", "off") in truthy
                else False
            )
        }
    )

    # set the string length limit (black default)
    config.update(
        {"fold_args_after": int(os.environ.get("ASTDOCS_FOLD_ARGS_AFTER", "88"))}
    )

    # if requested, show private objects in the output
    config.update(
        {
            "show_private": (
                True
                if os.environ.get("ASTDOCS_SHOW_PRIVATE", "off") in truthy
                else False
            )
        }
    )

    # if requested, split things up with %%% markers
    config.update({"split_by": os.environ.get("ASTDOCS_SPLIT_BY", "")})

    # if requested, add the line numbers to the source
    config.update(
        {
            "with_linenos": (
                True
                if os.environ.get("ASTDOCS_WITH_LINENOS", "off") in truthy
                else False
            )
        }
    )

    return config


def _update_templates(config: dict[str, typing.Any]):
    """Update the default templates according to the given configuration.

    Parameters
    ----------
    config : dict[str, typing.Any]
        Configuration options used to update the templates.
    """
    # keep (or not) the "%%%START ..." and "%%%END ..." markers
    if not config["bound_objects"]:
        TPL_CLASSDEF.template = re.sub(
            r"\n%%%[A-Z]+ CLASSDEF \$ancestry\.\$classname", "", TPL_CLASSDEF.template
        )
        TPL_FUNCTIONDEF.template = re.sub(
            r"\n%%%[A-Z]+ FUNCTIONDEF \$ancestry\.\$funcname",
            "",
            TPL_FUNCTIONDEF.template,
        )
        TPL_MODULE.template = re.sub(
            r"\n%%%[A-Z]+ MODULE \$module", "", TPL_MODULE.template
        )

    # add (or not) the "%%%BEGIN CLASSDEF ..." and "%%%END CLASSDEF ..." markers
    if "c" in config["split_by"]:
        TPL_CLASSDEF.template = (
            f"%%%BEGIN CLASSDEF $ancestry.$classname{TPL_CLASSDEF.template}"
        )

    # add (or not) the "%%%BEGIN FUNCTIONDEF ..." and "%%%END FUNCTIONDEF ..." markers
    if "f" in config["split_by"]:
        TPL_FUNCTIONDEF.template = (
            f"%%%BEGIN FUNCTIONDEF $ancestry.$funcname{TPL_FUNCTIONDEF.template}"
        )

    # add (or not) the "%%%BEGIN MODULE ..." and "%%%END MODULE ..." markers
    if "m" in config["split_by"]:
        TPL_MODULE.template = f"%%%BEGIN MODULE $module{TPL_MODULE.template}"

    # keep (or not) the "%%%SOURCE ...:...:..." markers
    if not config["with_linenos"]:
        TPL_CLASSDEF.template = TPL_CLASSDEF.template.replace(
            "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
        )
        TPL_FUNCTIONDEF.template = TPL_FUNCTIONDEF.template.replace(
            "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
        )


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

    The code blocks are extracted and replaced by placeholders before performing the
    substitutions (then rolled back in). The regular expressions are then applied:

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

    # extract code blocks, replace them by a placeholder
    blocks = []
    patterns = [f"([`]{{{i}}}.*?[`]{{{i}}})" for i in range(7, 2, -1)]
    i = 0
    for p in patterns:
        for m in re.finditer(p, s, flags=re.DOTALL):
            blocks.append(m.group(1))
            s = s.replace(m.group(1), f"%%%BLOCK{i}", 1)
            i += 1

    # remove trailing spaces
    s = re.sub(r" {1,}\n", r"\n", s)

    # rework any word preceded by one or more hashtag
    s = re.sub(r"\n#+\s*(.*)", r"\n**\1**", s)

    # rework any word followed by a line with 3 or more dashes
    s = re.sub(r"\n([A-Za-z ]+)\n-{3,}", r"\n**\1**\n", s)

    # rework list of arguments/descriptions (no types)
    s = re.sub(r"\n([A-Za-z0-9_ ]+)\n {2,}(.*)", r"\n* `\1`: \2", s)

    # rework list of arguments/types/descriptions
    s = re.sub(
        r"\n([A-Za-z0-9_ ]+) : ([A-Za-z0-9_\[\],\.| ]+)\n {2,}(.*)",
        r"\n* `\1` [`\2`]: \3",
        s,
    )

    # rework list of types/descriptions (return values)
    s = re.sub(r"\n: ([A-Za-z0-9_\[\],\.| ]+)\n {2,}(.*)", r"\n* [`\1`]: \2", s)

    # put the code blocks back in
    for i, b in enumerate(blocks):
        s = s.replace(f"%%%BLOCK{i}", b)

    return s.strip()


def parse_annotation(a: typing.Any) -> str:
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
    * The implementation only supports nodes I encountered in my projects.
    * Does not support `lambda` constructs.
    """
    # dig deeper: module.object
    if type(a) == ast.Attribute:
        return f"{parse_annotation(a.value)}.{a.attr}"

    # dig deeper: | operator
    if type(a) == ast.BinOp:
        s = parse_annotation(a.left)
        s += " | "
        s += parse_annotation(a.right)
        return s

    # dig deeper: @decorator(including=parameter)
    if type(a) == ast.Call:
        s = parse_annotation(a.func)
        s += "("
        s += ", ".join([f"{a_.arg}={parse_annotation(a_.value)}" for a_ in a.keywords])
        s += ")"
        return s

    # we dug deep enough and unravelled a value
    if type(a) == ast.Constant:
        if type(a.value) == str:
            return f'"{a.value}"'
        else:
            return str(a.value)

    # dig deeper: content within a dictionnary
    if type(a) == ast.Dict:
        s = "{"
        s += ", ".join(
            [
                f"{parse_annotation(k)}: {parse_annotation(v)}"
                for k, v in zip(a.keys, a.values)
            ]
        )
        s += "}"
        return s

    # dig deeper: content within a list
    if type(a) == ast.List:
        s = "["
        s += ", ".join([parse_annotation(a_) for a_ in a.elts])
        s += "]"
        return s

    # we dug deep enough and unravelled a canonical object
    if type(a) == ast.Name:
        return a.id

    # dig deeper: complex object, tuple[dict[int, float], bool, str] for instance
    if type(a) == ast.Subscript:
        v = parse_annotation(a.slice)
        s = parse_annotation(a.value)
        s += "["
        s += v[1:-1] if v.startswith("(") and v.endswith(")") else v
        s += "]"
        return s

    # dig deeper: content within a set
    if type(a) == ast.Set:
        s = "{"
        s += ", ".join([parse_annotation(a_) for a_ in a.elts])
        s += "}"
        return s

    # dig deeper: content within a tuple
    if type(a) == ast.Tuple:
        s = "("
        s += ", ".join([parse_annotation(a_) for a_ in a.elts])
        s += ")"
        return s

    return ""


def parse_class(
    node: ast.ClassDef,
    module: str,
    ancestry: str,
    classes: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
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
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    classes : dict[str, dict[str, str]]
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
        "hashtags": "#" if "c" in config["split_by"] else "###",
        "lineno": str(node.lineno),
    }

    return classes


def parse_function(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    module: str,
    ancestry: str,
    functions: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
) -> dict[str, dict[str, str]]:
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
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    functions : dict[str, dict[str, str]]
        Dictionnaries of all encountered function definitions.

    Notes
    -----
    If `*args` and some `kwargs` arguments are present, `args.vararg` will not be `None`
    and the `node.args.kwonlyargs`/`node.args.kw_defaults` attributes need to be parse.
    Otherwise all should be available in the `args`/`defaults` attributes.
    """
    ap = f"{ancestry}.{node.name}"  # absolute path to the object
    lp = ap.replace(module, "", 1).lstrip(".")  # local path to the object
    objects[module]["functions"][lp] = ap  # save the object path

    params = []  # formatted function/method parameters

    # parse decorator objects
    dc = [f"`@{parse_annotation(d)}`" for d in node.decorator_list]

    # parse/format arguments and annotations; with default values if present
    def _parse_format_argument(ann: typing.Any, val: typing.Any = None):
        """Parse and format an annotation.

        Parameters
        ----------
        ann : typing.Any
            Any type of annotation node.
        val : typing.Any
            Default value for this parameter.

        Returns
        -------
        : str
            Formatted annotation with potential default value.
        """
        s = ann.arg

        if ann.annotation is not None:
            s += ": "
            s += parse_annotation(ann.annotation)

        if val is not None:
            s += f" = {parse_annotation(val)}"

        return s

    # args; to accolate default values we need to reverse the argument list
    for ann, val in list(
        itertools.zip_longest(node.args.args[::-1], node.args.defaults[::-1])
    )[::-1]:
        params.append(_parse_format_argument(ann, val))

    # *args
    if node.args.vararg is not None:
        params.append(f"*{node.args.vararg.arg}")

    # kwargs, only populated if args.vararg is; same accolation comment as above
    for ann, val in list(
        itertools.zip_longest(node.args.kwonlyargs[::-1], node.args.kw_defaults[::-1])
    )[::-1]:
        params.append(_parse_format_argument(ann, val))

    # **kwargs
    if node.args.kwarg is not None:
        params.append(f"**{node.args.kwarg.arg}")

    # output
    if node.returns is not None:
        output = f" -> {parse_annotation(node.returns)}"
    else:
        output = ""

    # add line breaks if the function call is long (pre-render this latter first, no way
    # around it)
    if len(f'{node.name}({", ".join(params)}){output}') > config["fold_args_after"]:
        params = [f"\n    {p}" for p in params]
        suffix = ",\n"
    else:
        suffix = ""

    # save the object details
    functions[ap] = {
        "ancestry": ancestry,
        "params": ("," if len(suffix) else ", ").join(params) + suffix,
        "decoration": ("**Decoration** via " + ", ".join(dc) + ".") if dc else "",
        "endlineno": str(node.end_lineno),
        "funcdocs": format_docstring(node),
        "funcname": node.name,
        "hashtags": "#" if "f" in config["split_by"] else "###",
        "lineno": str(node.lineno),
        "output": output,
    }

    return functions


def parse_import(
    node: ast.Import | ast.ImportFrom,
    module: str,
    ancestry: str,
    imports: dict[str, str],
    config: dict[str, typing.Any] = config,
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
        Dictionnaries of parsed imports. Defaults to an empty dictionnary `{}`.
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    imports : dict[str, str]
        Dictionnaries of all encountered imports. Untouched for now, always empty
        dictionnary `{}`.
    """
    if type(node) == ast.Import:
        for n in node.names:
            abspath = f"{ancestry}.{n.name}"
            locpath = n.asname or n.name

            # save the object
            objects[module]["imports"][locpath] = abspath

    if type(node) == ast.ImportFrom:
        m = f"{node.module}." if node.module is not None else ""
        v = node.level + 1 if node.level > 0 else 0
        for n in node.names:
            abspath = f'{ancestry}.{"." * v}{m}{n.name}'
            locpath = n.asname or n.name

            # save the object; with support for heresy like "from .. import *" (who does
            # that seriously)
            objects[module]["imports"][locpath] = abspath

    return imports


def parse(
    node: typing.Any,
    module: str,
    ancestry: str = "",
    classes: dict[str, dict[str, str]] = {},
    functions: dict[str, dict[str, str]] = {},
    imports: dict[str, str] = {},
    config: dict[str, typing.Any] = config,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, str]]:
    """Recursively traverse the nodes of the abstract syntax tree.

    The present function calls the formatting function corresponding to the node name
    (if supported) to parse/format it.

    Parameters
    ----------
    node : typing.Any
        Any type of node to extract information from.
    module : str
        Name of the current module.
    ancestry : str
        Complete path to the object, used to identify ownership of children objects
        (functions and methods for instance).
    classes : dict[str, dict[str, str]]
        Dictionnaries of parsed class definitions. Defaults to an empty dictionnary
        `{}`.
    functions : dict[str, dict[str, str]]
        Dictionnaries of parsed function definitions. Defaults to an empty dictionnary
        `{}`.
    imports : dict[str, str]
        Dictionnaries of parsed imports. Defaults to an empty dictionnary `{}`.
    config : dict[str, typing.Any]
        Configuration options used to render attributes.

    Returns
    -------
    classes : dict[str, dict[str, str]]
        Dictionnaries of all encountered class definitions.
    functions : dict[str, dict[str, str]]
        Dictionnaries of all encountered function definitions.
    imports : dict[str, str]
        Dictionnaries of all encountered imports.
    """
    for n in node.body:

        # call the parser for each supported node type
        if n.__class__.__name__ == "ClassDef":
            classes = parse_class(n, module, ancestry, classes)

        elif n.__class__.__name__ in ("AsyncFunctionDef", "FunctionDef"):
            functions = parse_function(n, module, ancestry, functions)

        elif n.__class__.__name__ in ("Import", "ImportFrom"):
            imports = parse_import(n, module, ancestry, imports)

        # not interested
        else:
            pass

        # recursively traverse the ast
        try:
            parse(
                n,
                module,
                f"{ancestry}.{n.name}",
                classes,
                functions,
                imports,
            )
        except AttributeError:
            continue

    return classes, functions, imports


def render_class(
    filepath: str,
    name: str,
    classes: dict[str, dict[str, str]],
    functions: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
) -> str:
    """Render a `class` object, according to the defined `TPL_CLASSDEF` template.

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
        `Markdown`-formatted description of the class object.
    """
    ht = classes[name]["hashtags"]

    # select related methods
    fs = [f for f in functions.keys() if f.startswith(f"{name}.")]

    # fetch the content of __init__
    n = f"{name}.__init__"
    if n in fs:
        fs.remove(n)
        details = functions.pop(n)
        params = re.sub(r"self[\s,]*", "", details["params"], 1).strip()
        docstring = details["funcdocs"]
        beglineno = details["lineno"]
        endlineno = details["endlineno"]
        if config["with_linenos"]:
            docstring += f"\n\n%%%SOURCE {filepath}:{beglineno}:{endlineno}"
    else:
        params = ""
        docstring = ""

    # methods rendered
    fsr = []
    for f in fs:
        n = f.split(".")[-1]
        if not n.startswith("_") or config["show_private"]:
            functions[f].update(
                {
                    "hashtags": f"{ht}##",
                    "params": re.sub(
                        r"self[\s,]*", "", functions[f]["params"], 1
                    ).strip(),
                }
            )
            fsr.append(render_function(filepath, f, functions))

    # methods bullet list
    fsl = []
    for i, f in enumerate(fs):
        n = f.split(".")[-1]
        if not n.startswith("_") or config["show_private"]:
            link = f.replace(".", "").lower()  # github syntax
            desc = functions[f]["funcdocs"].split("\n")[0]
            desc = f": {desc}" if len(desc) else ""
            fsl.append(f"* [`{n}()`](#{link}){desc}")

    # update the description of the object
    classes[name].update(
        {
            "params": params,
            "constdocs": docstring,
            "functions": (ht + "# Methods\n\n" + "\n\n".join(fsr)) if fsr else "",
            "funcnames": ("**Methods**\n\n" + "\n".join(fsl)) if fsl else "",
            "path": filepath,
        }
    )

    return TPL_CLASSDEF.substitute(classes[name]).strip()


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
    # update the description of the object
    functions[name].update({"path": filepath})

    return TPL_FUNCTIONDEF.substitute(functions[name]).strip()


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
    fs = []
    for f in functions:
        if f.count(".") == name.count(".") + 1:
            n = f.split(".")[-1]
            if not n.startswith("_") or config["show_private"]:
                link = f.replace(".", "").lower()  # github syntax
                desc = functions[f]["funcdocs"].split("\n")[0]
                desc = f": {desc}" if len(desc) else ""
                fs.append(f"* [`{n}()`](#{link}){desc}")

    # classes bullet list
    cs = []
    for c in classes:
        if c.count(".") == name.count(".") + 1:
            n = c.split(".")[-1]
            if not n.startswith("_") or config["show_private"]:
                link = c.replace(".", "").lower()  # github syntax
                desc = classes[c]["classdocs"].split("\n")[0]
                desc = f": {desc}" if len(desc) else ""
                cs.append(f"* [`{n}`](#{link}){desc}")

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

    return TPL_MODULE.substitute(sub).strip()


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
        ancestry of the module. Defaults to empty string.
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
    _update_templates(config)

    if len(filepath):

        # clean up module name
        if remove_from_path:
            filepath = filepath.replace(remove_from_path, "")

        module = re.sub(r"\.py$", "", filepath.replace("/", ".")).lstrip(".")
        module = module.replace(".__init__", "")
        module = module if len(module) else os.getcwd().rsplit("/", 1)[-1]

        # traverse and parse the ast
        with open(filepath) as fp:
            n = ast.parse(fp.read())

    elif len(code) and len(module):
        filepath = f"{module}.py"
        n = ast.parse(code)

    else:
        return "Nothing to do."  # user provided nOthINg

    global objects  # all objects encountered over a whole run are kept track of
    objects[module] = {"classes": {}, "functions": {}, "imports": {}}

    # parse it all
    classes, functions, imports = parse(n, module, module, {}, {}, {})

    # render the functions at the root of the module
    fs = []
    for f in functions:
        if f.count(".") == module.count(".") + 1:
            name = f.split(".")[-1]
            if not name.startswith("_") or config["show_private"]:
                fs.append(render_function(filepath, f, functions, config))

    # render the classes at the root of the module
    cs = []
    for c in classes:
        if c.count(".") == module.count(".") + 1:
            name = c.split(".")[-1]
            if not name.startswith("_") or config["show_private"]:
                cs.append(render_class(filepath, c, classes, functions, config))

    # render each section according to provided options
    sub = {
        "classes": "\n\n".join(
            [
                "## Classes" if "c" not in config["split_by"] and cs else "",
                "\n\n".join(cs) if cs else "",
            ]
        ),
        "functions": "\n\n".join(
            [
                "## Functions" if "f" not in config["split_by"] and fs else "",
                "\n\n".join(fs) if fs else "",
            ]
        ),
        "module": render_module(
            module, format_docstring(n), classes, functions, config
        ),
    }

    s = TPL.substitute(sub).strip()

    # cleanup (extra line breaks)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\n{2,}%%%(^SOURCE[A-Z]*)", r"\n%%%\1", s)

    return s


def render_recursively(
    path: str, remove_from_path: str = "", config: dict[str, typing.Any] = config
) -> str:
    r"""Run pipeline on each `Python` module found in a folder and its subfolders.

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

    ```python
    import astdocs

    output_folder = "docs"

    for line in astdocs.render_recursively(...).split("\n"):
        if line.startswith("%%%BEGIN"):
            try:
                output.close()
            except NameError:
                pass
            x = line.split()[2].split(".")
            basename = f"{x[-1]}.md"
            dirname = f"{output_folder}/" + "/".join(x[:-1])
            os.makedirs(dirname, exist_ok=True)
            output = open(f"{dirname}/{basename}", "w")
        else:
            output.write(f"{line}\n")
    try:
        output.close()
    except NameError:
        pass
    ```
    """
    ms = []

    # render each module
    for filepath in sorted(glob.glob(f"{path}/**/*.py", recursive=True)):
        name = filepath.split("/")[-1]
        if not name.startswith("_") or config["show_private"] or name == "__init__.py":
            ms.append(
                render(
                    filepath=filepath, remove_from_path=remove_from_path, config=config
                )
            )

    s = "\n\n".join(ms)

    # cleanup (extra line breaks)
    s = re.sub(r"\n{2,}%%%(^SOURCE[A-Z]*)", r"\n%%%\1", s)

    return s


def postrender(func: typing.Callable) -> typing.Callable:
    """Apply a post-rendering function on the output of the decorated function.

    This can be used to streamline the linting of the output, or immediately convert to
    `HTML` for instance.

    Parameters
    ----------
    func : typing.Callable
        The function to apply; should take a `str` as lone input, the `Markdown` to
        process.

    Returns
    -------
    : str
        `Markdown`-formatted content.

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

    or a more concrete snippet:

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
    """

    def decorator(f: typing.Callable) -> typing.Callable:
        def wrapper(*args, **kwargs) -> typing.Callable:
            return func(f(*args, **kwargs))

        return wrapper

    return decorator


def cli():
    """Process CLI calls."""
    config = _update_configuration()

    if len(sys.argv) != 2:
        sys.exit("Wrong number of arguments! Accepting *one* only.")

    try:
        md = render(filepath=sys.argv[1], config=config)
    except IsADirectoryError:
        md = render_recursively(sys.argv[1], config=config)

    print(md)


if __name__ == "__main__":
    cli()
