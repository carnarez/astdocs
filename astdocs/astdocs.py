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

Each of these environment variables translates into a private attribute with the same
name: the `ASTDOCS_FOLD_ARGS_AFTER` value is stored in the `__FOLD_ARGS_AFTER__`
variable for instance.

Handling options completely programmatically breaks the `Python` idiomatic ways (code in
the middle of `import` statements):

```python
import os

os.environ["ASTDOCS_FOLD_ARGS_AFTER"] = 88
os.environ["ASTDOCS_WITH_LINENOS"] = "off"

import astdocs

md = astdocs.render_recursively(".")
```

and that might make some checkers/linters unhappy. (This whole thing started with two
flags but grew out of hands...)

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
    "\n$funcdefs"
    "\n%%%END CLASSDEF $ancestry.$classname"
)

TPL_FUNCTIONDEF: string.Template = string.Template(
    "\n%%%START FUNCTIONDEF $ancestry.$funcname"
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

# if requested, add markers indicating the start and end of an object definition
__BOUND_OBJECTS__: bool = (
    True
    if os.environ.get("ASTDOCS_BOUND_OBJECTS", "off") in ("1", "on", "true", "yes")
    else False
)

if not __BOUND_OBJECTS__:
    TPL_CLASSDEF.template = re.sub(
        r"\n%%%[A-Z]+ CLASSDEF \$ancestry\.\$classname", "", TPL_CLASSDEF.template
    )
    TPL_FUNCTIONDEF.template = re.sub(
        r"\n%%%[A-Z]+ FUNCTIONDEF \$ancestry\.\$funcname", "", TPL_FUNCTIONDEF.template
    )
    TPL_MODULE.template = re.sub(
        r"\n%%%[A-Z]+ MODULE \$module", "", TPL_MODULE.template
    )

# set the string length limit (black default)
__FOLD_ARGS_AFTER__: int = int(os.environ.get("ASTDOCS_FOLD_ARGS_AFTER", "88"))

# if requested, show private objects in the output
__SHOW_PRIVATE__: bool = (
    True
    if os.environ.get("ASTDOCS_SHOW_PRIVATE", "off") in ("1", "on", "true", "yes")
    else False
)

# if requested, split things up with %%% markers
__SPLIT_BY__: str = os.environ.get("ASTDOCS_SPLIT_BY", "")

if "c" in __SPLIT_BY__:
    TPL_CLASSDEF.template = (
        f"%%%BEGIN CLASSDEF $ancestry.$classname{TPL_CLASSDEF.template}"
    )

if "f" in __SPLIT_BY__:
    TPL_FUNCTIONDEF.template = (
        f"%%%BEGIN FUNCTIONDEF $ancestry.$funcname{TPL_FUNCTIONDEF.template}"
    )

if "m" in __SPLIT_BY__:
    TPL_MODULE.template = f"%%%BEGIN MODULE $module{TPL_MODULE.template}"

# if requested, add the line numbers to the source
__WITH_LINENOS__: bool = (
    True
    if os.environ.get("ASTDOCS_WITH_LINENOS", "off") in ("1", "on", "true", "yes")
    else False
)

if not __WITH_LINENOS__:
    TPL_CLASSDEF.template = TPL_CLASSDEF.template.replace(
        "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
    )
    TPL_FUNCTIONDEF.template = TPL_FUNCTIONDEF.template.replace(
        "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
    )

_classdefs = {}
_funcdefs = {}
_module = ""

objects: dict[str, typing.Any] = {}


def format_annotation(a: typing.Any, char: str = "") -> str:
    """Format an annotation (object type or decorator).

    Dive as deep as necessary within the children nodes until reaching the name of the
    module/attribute objects are annotated after; save the import path on the way.
    Recursively repeat for complicated object.

    See the code itself for some line-by-line documentation.

    Parameters
    ----------
    a : typing.Any
        The starting node to extract annotation information from.
    char : str
        The additional character to place at the beginning of the annotation; `"@"` for
        a decorator, `" -> "` for a return type, *etc.* (defaults to empty string).

    Returns
    -------
    : str
        The formatted annotation.

    Known problems
    --------------
    * Does not support `lambda` functions.
    * Does not support content within `dict`/`list`/`set`/`tuple` objects.
    """
    s = ""

    if a is not None:
        path: list[str] = []

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

        # but the deepest object might be something else, and we need to recursively
        # track it once again (it is the case for the new-ish "or" operator)
        if hasattr(o, "right"):
            path.insert(0, f"{format_annotation(o.right)}")
            if hasattr(o, "left"):
                path.insert(0, format_annotation(o.left))

        # some functions/methods simply return nothing
        if o is None:
            path.insert(0, "None")

        # add to the string; beware of the new-ish "or" operator
        if hasattr(o, "right"):
            s += f'{char}{" | ".join(path)}'
        else:
            s += f'{char}{".".join(path)}'

    # the annotation itself might be complex and completed by other annotations (think
    # the complicated type description enforced by mypy for instance)
    if hasattr(a, "slice"):
        try:
            s += f'[{", ".join([format_annotation(a_) for a_ in a.slice.value.elts])}]'
        except AttributeError:
            pass  # a.slice.value or a.slice.value.elts attributes do not exist
        else:
            s += format_annotation(a.slice.value)

    # another complicated case: decorator with arguments
    if hasattr(a, "func"):
        s += format_annotation(a.func)
        s += f'({", ".join([format_annotation(a_) for a_ in a.args])})'

    return s


def format_docstring(
    n: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module,
) -> str:
    r"""Format the object docstring.

    Expect some stiff `NumPy`-ish formatting (see
    [this](https://numpydoc.readthedocs.io/en/latest/example.html#example) or
    [that](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html)).
    Do try to **type** all your input parameters/returned objects. And use a linter on
    the output?

    Parameters
    ----------
    n : ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
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
    n : ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
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

    def format_docstring(n: ast.*) -> str:  # simple wrapper function
        return my_docstring_parser(ast.get_docstring(n))

    astdocs.format_docstring = format_docstring

    print(astdocs.render(...))
    ```

    Known problem
    -------------
    Overall naive, stiff and *very* opinionated (again, for *my* use).
    """
    s = ast.get_docstring(n) or ""

    # extract code blocks, replace them by a placeholder
    blocks = []
    patterns = [r"([`]{4}.*?[`]{4})", r"([`]{3}.*?[`]{3})"]
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


def parse_classdef(n: ast.ClassDef):
    """Parse a `class` statement.

    Parameters
    ----------
    n : ast.ClassDef
        The node to extract information from.
    """
    # determine the title level
    if "c" in __SPLIT_BY__:
        ht = "#"
    else:
        ht = "###"

    # parse decorator objects
    dc = [f'`{format_annotation(d, "@")}`' for d in n.decorator_list]

    # save the interesting details (more to come during rendering)
    _classdefs[f"{n.ancestry}.{n.name}"] = {  # type: ignore
        "ancestry": n.ancestry,  # type: ignore
        "classname": n.name,
        "classdocs": format_docstring(n),
        "decoration": "**Decoration** via " + ", ".join(dc) + "." if dc else "",
        "endlineno": n.end_lineno,
        "hashtags": ht,
        "lineno": n.lineno,
    }

    # save the object
    absolute = f"{n.ancestry}.{n.name}"  # type: ignore
    local = absolute.replace(f"{_module}", "", 1).lstrip(".")
    objects[_module]["classes"][local] = absolute


def parse_functiondef(n: ast.AsyncFunctionDef | ast.FunctionDef):
    """Parse a `def` statement.

    Parameters
    ----------
    n : ast.AsyncFunctionDef | ast.FunctionDef
        The node to extract information from.
    """
    # determine the title level
    if "f" in __SPLIT_BY__:
        ht = "#"
    else:
        ht = "###"

    # parse decorator objects
    dc = [f'`{format_annotation(d, "@")}`' for d in n.decorator_list]

    # parse/format arguments and annotations
    params = [f'{a.arg}{format_annotation(a.annotation, ": ")}' for a in n.args.args]
    if n.args.vararg is not None:
        params += [f"*{n.args.vararg.arg}"]
    if n.args.kwarg is not None:
        params += [f"**{n.args.kwarg.arg}"]
    returns = format_annotation(n.returns, " -> ")

    # add line breaks if the function call is long (pre-render this latter first, no way
    # around it)
    rendered = f'{n.name}({", ".join(params)}){returns}'
    if len(rendered) > __FOLD_ARGS_AFTER__:
        params = [f"\n    {p}" for p in params]
        suffix = ",\n"
    else:
        suffix = ""

    # save the interesting details
    _funcdefs[f"{n.ancestry}.{n.name}"] = {  # type: ignore
        "ancestry": n.ancestry,  # type: ignore
        "params": ", ".join(params) + suffix,
        "decoration": ("**Decoration** via " + ", ".join(dc) + ".") if dc else "",
        "endlineno": n.end_lineno,
        "funcdocs": format_docstring(n),
        "funcname": n.name,
        "hashtags": ht,
        "lineno": n.lineno,
        "returns": returns,
    }

    # save the object
    absolute = f"{n.ancestry}.{n.name}"  # type: ignore
    local = absolute.replace(f"{_module}", "", 1).lstrip(".")
    objects[_module]["functions"][local] = absolute


def parse_import(n: ast.Import | ast.ImportFrom):
    """Parse `import ... [as ...]` and `from ... import ... [as ...]` statements.

    The content built by this function is currently *not* used. This latter is kept in
    case all the objects (and aliases) accessible within a module is required for a
    post-processing or some later smart implementations.

    Parameters
    ----------
    n : ast.Import | ast.ImportFrom
        The node to extract information from.
    """
    path = ""
    level = 0

    if hasattr(n, "module"):
        if n.module is None:  # type: ignore
            if n.level == 0:  # type: ignore
                path = ".".join(n.ancestry.split(".")[:-1])  # type: ignore
        else:
            path = n.module  # type: ignore

        if n.level > 0:  # type: ignore
            level = n.level  # type: ignore

    for i in n.names:
        if i.asname is not None:
            local = i.asname
        else:
            local = i.name

        # save the object
        # support for heresy like "from .. import *"
        absolute = "." * level + f"{path}.{i.name}".lstrip(".")
        local = absolute if local == "*" else local
        objects[_module]["imports"][local] = absolute


def parse_tree(n: typing.Any):
    """Recursively traverse the nodes of the abstract syntax tree.

    The present function calls the formatting function corresponding to the node name
    (if supported) to parse/format it.

    Add an `.ancestry` attribute on each traversed children object containing the
    complete path to that object. This path is used to identify ownership of objects
    (function *vs.* method for instance).

    Parameters
    ----------
    n : typing.Any
        Any type of node to extract information from.
    """
    if hasattr(n, "name"):
        name = n.name
    else:
        name = n.__class__.__name__

    for c in n.body:

        # adding an "ancestry" attribute here, triggering some mypy complains and
        # some "type: ignore" here and there
        if hasattr(n, "ancestry"):
            c.ancestry = f"{n.ancestry}.{name}"
        else:
            c.ancestry = name

        func = "parse_" + (
            c.__class__.__name__.lower()
            .replace("async", "")
            .replace("importfrom", "import")
        )
        if func in globals():
            globals()[func](c)  # haha, nasty

        try:
            parse_tree(c)
        except AttributeError:
            continue


def render_classdef(filepath: str, name: str) -> str:
    """Render a `class` object, according to the defined `TPL_CLASSDEF` template.

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
        _ = _funcdefs.pop(init)
        params = re.sub(r"self(?:,)?", "", _["params"]).strip()
        docstr = _["funcdocs"]
        lineno = _["lineno"]
        endlineno = _["endlineno"]
        if __WITH_LINENOS__:
            docstr += f"\n\n%%%SOURCE {filepath}:{lineno}:{endlineno}"
    else:
        params = ""
        docstr = ""

    # render all methods
    fr = []
    for f in fn:
        n = f.split(".")[-1]
        if not n.startswith("_") or __SHOW_PRIVATE__:
            _funcdefs[f].update(
                {
                    "hashtags": f"{ht}##",
                    "params": re.sub(r"self(?:,)?", "", _funcdefs[f]["params"]).strip(),
                }
            )
            fr.append(render_functiondef(filepath, f))

    # methods bullet list
    # clobber the previous list (in case we need to take the private method out)
    fn_ = []
    for i, f in enumerate(fn):
        n = f.split(".")[-1]
        if not n.startswith("_") or __SHOW_PRIVATE__:
            link = f.replace(".", "").lower()  # github syntax
            desc = _funcdefs[f]["funcdocs"].split("\n")[0]
            fn_.append(f"* [`{n}()`](#{link}): {desc}")
    fn = fn_

    # update the description of the object
    _classdefs[name].update(
        {
            "params": params,
            "constdocs": docstr,
            "funcdefs": (ht + "# Methods\n\n" + "\n\n".join(fr)) if fr else "",
            "funcnames": ("**Methods**\n\n" + "\n".join(fn)) if fn else "",
            "path": filepath,
        }
    )

    return TPL_CLASSDEF.substitute(_classdefs[name]).strip()


def render_functiondef(filepath: str, name: str) -> str:
    """Render a `def` object (function or method).

    Follow the defined `TPL_FUNCTIONDEF` template.

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

    return TPL_FUNCTIONDEF.substitute(_funcdefs[name]).strip()


def render_module(name: str, docstring: str = "") -> str:
    """Render a module summary as a `Markdown` file.

    Follow the defined `TPL_MODULE` template.

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
            if not n.startswith("_") or __SHOW_PRIVATE__:
                link = f.replace(".", "").lower()  # github syntax
                desc = _funcdefs[f]["funcdocs"].split("\n")[0]
                fn.append(f"* [`{n}()`](#{link}): {desc}")

    # classes bullet list
    cn = []
    for c in _classdefs:
        if c.count(".") == name.count(".") + 1:
            n = c.split(".")[-1]
            if not n.startswith("_") or __SHOW_PRIVATE__:
                link = c.replace(".", "").lower()  # github syntax
                desc = _classdefs[c]["classdocs"].split("\n")[0]
                cn.append(f"* [`{n}`](#{link}): {desc}")

    sub = {
        "classnames": "**Classes**\n\n" + "\n".join(cn) if cn else "",
        "docstring": docstring,
        "funcnames": "**Functions**\n\n" + "\n".join(fn) if fn else "",
        "module": name,
    }

    # clean up the unwanted
    if "c" in __SPLIT_BY__:
        sub["classnames"] = ""
    if "f" in __SPLIT_BY__:
        sub["funcnames"] = ""

    return TPL_MODULE.substitute(sub).strip()


def render(filepath: str, remove_from_path: str = "") -> str:
    """Run the whole pipeline (useful wrapper function when this gets used as a module).

    Parameters
    ----------
    filepath : str
        The path to the module to process.
    remove_from_path : str
        Part of the path to be removed. If one is rendering the content of a file buried
        deep down in a complicated folder tree *but* does not want this to appear in the
        ancestry of the module.

    Returns
    -------
    : str
        `Markdown`-formatted content.
    """
    global _classdefs
    global _funcdefs
    global _module
    global objects

    # make sure to flush the [global] objects in case multiple are rendered
    # note all objects encountered over a whole package are kept track of
    _classdefs = {}
    _funcdefs = {}

    with open(filepath) as _:

        # module ancestry
        if remove_from_path:
            filepath = filepath.replace(remove_from_path, "")
        m = re.sub(r"\.py$", "", filepath.replace("/", ".")).lstrip(".")

        # define the name of the current module
        _module = m.replace(".__init__", "")
        _module = _module if len(_module) else os.getcwd().rsplit("/", 1)[-1]
        objects[_module] = {"classes": {}, "functions": {}, "imports": {}}

        # traverse the ast
        n = ast.parse(_.read())
        n.name = _module  # type: ignore
        parse_tree(n)

    # only the objects at the root of the module
    fr = []
    for f in _funcdefs:
        if f.count(".") == n.name.count(".") + 1:  # type: ignore
            name = f.split(".")[-1]
            if not name.startswith("_") or __SHOW_PRIVATE__:
                fr.append(render_functiondef(filepath, f))

    cr = []
    for c in _classdefs:
        if c.count(".") == n.name.count(".") + 1:  # type: ignore
            name = c.split(".")[-1]
            if not name.startswith("_") or __SHOW_PRIVATE__:
                cr.append(render_classdef(filepath, c))

    # render each section
    sub = {
        "classes": "\n\n".join(
            [
                "## Classes" if "c" not in __SPLIT_BY__ and cr else "",
                "\n\n".join(cr) if cr else "",
            ]
        ),
        "functions": "\n\n".join(
            [
                "## Functions" if "f" not in __SPLIT_BY__ and fr else "",
                "\n\n".join(fr) if fr else "",
            ]
        ),
        "module": render_module(n.name, format_docstring(n)),  # type: ignore
    }

    s = TPL.substitute(sub).strip()

    # cleanup (extra line breaks)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\n{2,}%%%(^SOURCE[A-Z]*)", r"\n%%%\1", s)

    return s


def render_recursively(path: str, remove_from_path: str = "") -> str:
    r"""Run pipeline on each `Python` module found in a folder and its subfolders.

    Parameters
    ----------
    path : str
        The path to the folder to process.
    remove_from_path : str
        Part of the path to be removed.

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
    mr = []

    # render each module
    for filepath in sorted(glob.glob(f"{path}/**/*.py", recursive=True)):
        name = filepath.split("/")[-1]
        if not name.startswith("_") or __SHOW_PRIVATE__ or name == "__init__.py":
            mr.append(render(filepath, remove_from_path))

    s = "\n\n".join(mr)

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
    if len(sys.argv) != 2:
        sys.exit("Wrong number of arguments! Accepting *one* only.")

    try:
        md = render(sys.argv[1])
    except IsADirectoryError:
        md = render_recursively(sys.argv[1])

    print(md)


if __name__ == "__main__":
    cli()
