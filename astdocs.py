r"""Extract and format documentation from `Python` code.

In more details, parse the underlying Abstract Syntax Tree (AST) description. (See
[documentation](https://docs.python.org/3/library/ast.html) of the standard library
module with same name.)

The only requirement is to use the standard library **exclusively** (even the
[templating](https://docs.python.org/3/library/string.html#template-strings)), and keep
it as lean as possible. Support for corner cases is scarse... for one, no
class-in-function (or the opposite), or function-in-function (considered private).

The simplest way to check this is to run it on itself:

```shell
$ python astdocs.py astdocs.py
```

or even:

```shell
$ for f in $(find . -name "*.py"); do
>   python astdocs.py $f > ${f/py/md}
> done
```

The behaviour of this little stunt can be modified via environment variables:

* `ASTDOCS_FOLD_ARGS_AFTER` to fold long object (function/method) definition (many
  parameters). Defaults to 3.
* `ASTDOCS_SPLIT_BY` taking the `m` (default), `mc` or `mfc`: split each [m]odule,
  [f]unction and [c]lass apart (by adding `%%%BX` markers in the output, `X` being
  either `F` -functions/methods- or `C` -classes). Classes will always keep their
  methods. In case `mfc` is provided, the module will only keep its docstring, and
  each function will be marked.
* `ASTDOCS_WITH_LINENOS` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored) to show the line numbers of the object in the code source (to be
  processed later on by your favourite `Markdown` renderer). Look for the `%%%SOURCE`
  marker.

```shell
$ ASTDOCS_WITH_LINENOS=on python astdocs.py astdocs.py
```

or to split marked sections:

```shell
$ ASTDOCS_SPLIT_BY=mfc python astdocs.py module.py | csplit -qz - '/%%%B/' '{*}'
$ mv xx00 module.md
$ mkdir module
$ for f in xx??; do
>   path=$(grep -m1 '^#' $f | sed -r 's|#{1,} \`(.*)\`|\1|g;s|\.|/|g')
>   grep -v '^%%%' $f > "$path.md"  # quotes are needed
>   rm $f
> done
```

If the regular expression solution presented here (which works for *my* needs) does not
fulfill, it is pretty easy to clobber it:

```python
import ast
import astdocs

def my_docstring_parser(docstring: str) -> str:
    # process docstring
    return string

def format_docstring(n):
    return my_docstring_parser(ast.get_docstring(n))

astdocs.format_docstring = format_docstring

print(astdocs.render(...))
```

Attributes
----------
CLASSDEF_TPL : string.Template
    Template to render `class` objects.
FUNCTIONDEF_TPL : string.Template
    Template to render `def` objects (async or not).
SUMMARY_TPL : string.Template
    Template to render the module summary.
TPL : string.Template
    Template to render the overall page (only governs order of objects in the output).
"""

import ast
import os
import re
import string
import sys
import typing

CLASSDEF_TPL = string.Template(
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
    "\n$funcdefs"
)

FUNCTIONDEF_TPL = string.Template(
    "\n$hashtags `$ancestry.$funcname`"
    "\n"
    "\n```python"
    "\n$funcname($params)$returns:"
    "\n```"
    "\n"
    "\n$funcdocs"
    "\n"
    "\n$decoration"
    "\n"
    "\n%%%SOURCE $path:$lineno:$endlineno"
)

SUMMARY_TPL = string.Template(
    "\n# Module `$module`\n\n$docstring\n\n$funcnames\n\n$classnames"
)

TPL = string.Template("$summary\n\n$functions\n\n$classes")

# if requested, split things up with %%% markers
_split_by = os.environ.get("ASTDOCS_SPLIT_BY", "m")
if "c" in _split_by:
    CLASSDEF_TPL.template = "%%%BC" + CLASSDEF_TPL.template
if "f" in _split_by:
    FUNCTIONDEF_TPL.template = "%%%BF" + FUNCTIONDEF_TPL.template

# if requested, add the line numbers to the source
if os.environ.get("ASTDOCS_WITH_LINENOS", "off") not in ("1", "on", "true", "yes"):
    CLASSDEF_TPL.template = CLASSDEF_TPL.template.replace(
        "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
    )
    FUNCTIONDEF_TPL.template = FUNCTIONDEF_TPL.template.replace(
        "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
    )


_classdefs = {}
_funcdefs = {}


def format_annotation(a: typing.Union[ast.Attribute, ast.Name], char: str = "") -> str:
    """Format an annotation (object type or decorator).

    Dive as deep as necessary within the children nodes until reaching the name of the
    module/attribute objects are annotated after; save the import path on the way.
    Recursively repeat for complicated object.

    See the code itself for some line-by-line documentation.

    Parameters
    ----------
    a : typing.Union[ast.Attribute, ast.Name]
        The starting node to extract annotation information from.
    char : str
        The additional character to place at the beginning of the annotation; `"@"` for
        a decorator, `" -> "` for a return type, *etc.* (defaults to empty string).

    Returns
    -------
    : str
        The formatted annotation.
    """
    s = ""

    if a is not None:
        path = []

        # dig deeper (hence the insert(0) instead of append) until finding the name
        # (coined as "id") of the object; the content of the "attr" keys found on the
        # way are the sub-modules
        o = a
        while not hasattr(o, "id"):
            if hasattr(o, "attr"):
                path.insert(0, o.attr)
            try:
                o = o.value
            except AttributeError:
                break

        # we dug deep enough and unravelled it
        if hasattr(o, "id"):
            path.insert(0, o.id)

        # if the final object is a string, that also works
        if type(o) == str:
            path.insert(0, o)

        # but the deepest object might be something else, and we need to recursively
        # track it once again (it is the case for list, tuple or dict for instance)
        if hasattr(o, "elts"):
            path.insert(0, f'[{", ".join([format_annotation(a_) for a_ in o.elts])}]')

        # some functions/methods simply return nothing
        if o is None:
            path.insert(0, "None")

        # add to the string
        s += f'{char}{".".join(path)}'

    # the annotation itself might be complex and completed by other annotations (think
    # the complicated type description enforced by mypy for instance)
    if hasattr(a, "slice"):
        if hasattr(a.slice.value, "elts"):
            s += f'[{", ".join([format_annotation(a_) for a_ in a.slice.value.elts])}]'
        else:
            s += format_annotation(a.slice.value)

    return s


def format_docstring(
    n: typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module]
) -> str:
    """Format the object docstring.

    Expect some stiff `NumPy`-ish formatting (see
    [this](https://numpydoc.readthedocs.io/en/latest/example.html#example) or
    [that](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html)).
    Do try to **type** all your input parameters/returned objects. And use a linter on
    the output.

    Parameters
    ----------
    n : typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module]
        Source node to extract/parse docstring from.

    Returns
    -------
    : str
        The formatted docstring.

    Known problems
    --------------
    * Overall naive and *very* opinionated (for my use).
    * Does not support list in parameter/return entries.
    """
    s = ast.get_docstring(n) or ""

    # remove trailing spaces
    s = re.sub(r" {1,}\n", r"\n", s)

    # rework any word preceded by one or more hashtag
    s = re.sub(r"\n[#{1,}] (\w+)", r"\n**\1:**\n", s)

    # rework any word followed by a line with 3 or more dashes
    s = re.sub(r"\n([A-Za-z ]+)\n-{3,}", r"\n**\1:**\n", s)

    # rework list of arguments/descriptions (no types)
    s = re.sub(r"\n([A-Za-z0-9_ ]+)\n {2,}(.*)", r"\n* [`\1`]: \2", s)

    # rework list of arguments/types/descriptions
    s = re.sub(
        r"\n([A-Za-z0-9_ ]+) : ([A-Za-z0-9_\[\],\. ]+)\n {2,}(.*)",
        r"\n* `\1` [`\2`]: \3",
        s,
    )

    # rework list of types/descriptions (return values)
    s = re.sub(r"\n: ([A-Za-z0-9_\[\],\. ]+)\n {2,}(.*)", r"\n* [`\1`]: \2", s)

    return s.strip()


def parse_classdef(n: ast.ClassDef):
    """Parse a `class` statement.

    Parameters
    ----------
    n : ast.ClassDef
        The node to extract information from.
    """
    # determine the title level
    if "c" in _split_by:
        ht = "#"
    else:
        ht = "###"

    # parse decorator objects
    dc = [f'`{format_annotation(d, "@")}`' for d in n.decorator_list]

    if not n.name.startswith("_"):
        _classdefs[f"{n.ancestry}.{n.name}"] = {
            "ancestry": n.ancestry,
            "classname": n.name,
            "classdocs": format_docstring(n),
            "decoration": "**Decoration:** via " + ", ".join(dc) + "." if dc else "",
            "endlineno": n.end_lineno,
            "hashtags": ht,
            "lineno": n.lineno,
        }


def parse_functiondef(n: typing.Union[ast.AsyncFunctionDef, ast.FunctionDef]):
    """Parse a `def` statement.

    Parameters
    ----------
    n : typing.Union[ast.AsyncFunctionDef, ast.FunctionDef]
        The node to extract information from.
    """
    # determine the title level
    if "f" in _split_by:
        ht = "#"
    else:
        ht = "###"

    # parse decorator objects
    dc = [f'`{format_annotation(d, "@")}`' for d in n.decorator_list]

    # argument gets its own line if many parameters
    if len(n.args.args) > os.environ.get("ASTDOCS_FOLD_ARGS_AFTER", 3):
        prefix = "\n    "
    else:
        prefix = ""

    # parse arguments
    params = [
        f'{prefix}{a.arg}{format_annotation(a.annotation, ": ")}' for a in n.args.args
    ]

    if not n.name.startswith("_"):
        _funcdefs[f"{n.ancestry}.{n.name}"] = {
            "ancestry": n.ancestry,
            "params": ", ".join(params) + ("\n" if len(prefix) else ""),
            "decoration": ("**Decoration** via " + ", ".join(dc) + ".") if dc else "",
            "endlineno": n.end_lineno,
            "funcdocs": format_docstring(n),
            "funcname": n.name,
            "hashtags": ht,
            "lineno": n.lineno,
            "returns": format_annotation(n.returns, " -> "),
        }


def parse_tree(n: typing.Any):
    """Recursively traverse the nodes of the abstract syntax tree.

    The present function calls the formatting function corresponding to the node name
    (if supported) to parse/format it.

    Add an `.ancestry` attribute on each traversed children object containing the
    complete path to that object. This path is used to identify ownership of objects
    (function *vs.* method for instance).

    Parameters
    ----------
    n
        Any type of node to extract information from.
    """
    if hasattr(n, "name"):
        name = n.name
    else:
        name = n.__class__.__name__

    for c in n.body:

        if hasattr(n, "ancestry"):
            c.ancestry = f"{n.ancestry}.{name}"
        else:
            c.ancestry = name

        func = f'parse_{c.__class__.__name__.lower().replace("async", "")}'
        if func in globals():
            globals()[func](c)

        try:
            parse_tree(c)
        except AttributeError:
            continue


def render_classdef(filepath: str, name: str) -> str:
    """Render a `class` object, according to the defined `CLASSDEF_TPL` template.

    Parameters
    ----------
    filepath : str
        Path to the module (file) defining the object.
    name : str
        The name (full path including all ancestors) of the object to render.

    Returns
    -------
    : str
        `Markdown`-formatted description of the class object.
    """
    ht = _classdefs[name]["hashtags"]

    # select related methods
    fn = [f for f in _funcdefs if f.startswith(f"{name}.")]

    # fetch the content of __init__
    init = f"{name}.__init__"
    if init in fn:
        fn.pop(fn.index(init))
        fd = _funcdefs.pop(init)
        params = fd["params"]
        docstr = fd["constdocs"]
    else:
        params = ""
        docstr = ""

    # render all methods
    fd = []
    for f in fn:
        _funcdefs[f].update({"hashtags": f"{ht}##"})
        fd.append(render_functiondef(filepath, f))

    # methods bullet list
    for i, f in enumerate(fn):
        n = f.split(".")[-1]
        link = f.replace(".", "").lower()  # github/mdbook
        fn[i] = f"* [`{n}()`](#{link})"

    # update the description of the object
    _classdefs[name].update(
        {
            "params": params,
            "constdocs": docstr,
            "funcdefs": (ht + "# Methods\n\n" + "\n\n".join(fd)) if fd else "",
            "funcnames": ("**Methods:**\n\n" + "\n".join(fn)) if fn else "",
            "path": filepath,
        }
    )

    return CLASSDEF_TPL.substitute(_classdefs[name]).strip()


def render_functiondef(filepath: str, name: str) -> str:
    """Render a `def` object (function or method).

    Follow the defined `FUNCTIONDEF_TPL` template.

    Parameters
    ----------
    filepath : str
        Path to the module (file) defining the object.
    name : str
        The name (full path including all ancestors) of the object to render.

    Returns
    -------
    : str
        `Markdown`-formatted description of the function/method object.
    """
    # update the description of the object
    _funcdefs[name].update({"path": filepath})

    return FUNCTIONDEF_TPL.substitute(_funcdefs[name]).strip()


def render_summary(name: str, docstring: str = "") -> str:
    """Render a module summary as a `Markdown` file.

    Follow the defined `SUMMARY_TPL` template.

    Parameters
    ----------
    name : str
        Name of the module being parsed.
    docstring : str
        The docstring of the module itself, if present (defaults to an empty string).

    Returns
    -------
    : str
        `Markdown`-formatted description of the whole module.
    """
    # self-standing functions bullet list
    fn = []
    for f in _funcdefs:
        if f.count(".") == name.count(".") + 1:
            n = f.split(".")[-1]
            link = f.replace(".", "").lower()  # github/mdbook
            fn.append(f"* [`{n}()`](#{link})")

    # classes bullet list
    cn = []
    for c in _classdefs:
        if c.count(".") == name.count(".") + 1:
            n = c.split(".")[-1]
            link = c.replace(".", "").lower()  # github/mdbook
            cn.append(f"* [`{n}`](#{link})")

    sub = {
        "classnames": "**Classes:**\n\n" + "\n".join(cn) if cn else "",
        "docstring": docstring,
        "funcnames": "**Functions:**\n\n" + "\n".join(fn) if fn else "",
        "module": name,
    }

    # clean up the unwanted
    if "c" in _split_by:
        sub["classnames"] = ""
    if "f" in _split_by:
        sub["funcnames"] = ""

    return SUMMARY_TPL.substitute(sub).strip()


def render(filepath: str) -> str:
    """Run the whole pipeline (wrapper method).

    Parameters
    ----------
    filepath : str
        The path to the module to process.

    Returns
    -------
    : str
        `Markdown`-formatted content.
    """
    with open(filepath) as f:
        m = filepath.replace("/", ".").replace(".py", "")

        # traverse the ast
        n = ast.parse(f.read())
        n.name = m.replace(".__init__", "")
        parse_tree(n)

    # only the objects at the root of the module
    fr = [
        render_functiondef(filepath, f)
        for f in _funcdefs
        if f.count(".") == n.name.count(".") + 1
    ]
    cr = [
        render_classdef(filepath, c)
        for c in _classdefs
        if c.count(".") == n.name.count(".") + 1
    ]

    # render each section
    sub = {
        "classes": "\n\n".join(
            [
                "## Classes" if "c" not in _split_by and cr else "",
                "\n\n".join(cr) if cr else "",
            ]
        ),
        "functions": "\n\n".join(
            [
                "## Functions" if "f" not in _split_by and fr else "",
                "\n\n".join(fr) if fr else "",
            ]
        ),
        "summary": render_summary(n.name, format_docstring(n)),
    }

    s = TPL.substitute(sub).strip()
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\n{2,}%%%B", "\n%%%B", s)

    return s


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit(
            "Too many arguments!"
            f'Please read the docs via `pydoc {sys.argv[0].replace(".py", "")}` or so.'
        )
    print(render(sys.argv[1]))
