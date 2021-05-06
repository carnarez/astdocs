r"""Extract and format documentation from `Python` code.

*According to **my** standards.*

In a few more words, parse the underlying Abstract Syntax Tree (AST) description. (See
the [documentation](https://docs.python.org/3/library/ast.html) of the standard library
module with same name.) It expects a relatively clean input (demonstrated in this very
script) which forces me to keep my code somewhat correctly documented and without fancy
syntax.

My only requirement was to use the `Python` standard library **exclusively** (even the
[templating](https://docs.python.org/3/library/string.html#template-strings)) as it is
quite [overly] complete these day, and keep it as *lean* as possible. Support for corner
cases is scarse... for one, no class-in- nor function-in-function (which I consider
private, in the `Python` sense).

The simplest way to check by example is to run this script on itself:

```shell
$ python astdocs.py astdocs.py  # pipe it to your favourite markdown linter
```

or even:

```shell
$ for f in $(find . -name "*.py"); do
>   python astdocs.py $f > ${f/py/md}
> done
```

The behaviour of this little stunt can be modified via environment variables:

* `ASTDOCS_FOLD_ARGS_AFTER` to fold long object (function/method) definitions (many
  parameters). Defaults to 88 characters, [`black`](https://github.com/psf/black)
  [recommended](https://www.youtube.com/watch?v=wf-BqAjZb8M&t=260s&ab_channel=PyCon2015)
  default.
* `ASTDOCS_SHOW_PRIVATE` taking the `1`, `on`, `true` or `yes` values (anything else
   will be ignored/counted as negative) to show `Python` private objects (which names
   start with an underscore).
* `ASTDOCS_SPLIT_BY` taking the `m`, `mc`, `mfc` or an empty value (default, all
  rendered content in one output): split each **m**odule, **f**unction and/or **c**lass
  (by adding `%%%BEGIN ...` markers). Classes will always keep their methods. In case
  `mfc` is provided, the module will only keep its docstring, and each function will be
  marked.
* `ASTDOCS_WITH_LINENOS` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored) to show the line numbers of the object in the code source (to be
  processed later on by your favourite `Markdown` renderer). Look for the `%%%SOURCE`
  markers.

```shell
$ ASTDOCS_WITH_LINENOS=on python astdocs.py astdocs.py
```

or to split marked sections:

```shell
$ ASTDOCS_SPLIT_BY=mc python astdocs.py module.py | csplit -qz - '/%%%BEGIN/' '{*}'
$ mv xx00 module.md
$ mkdir module
$ for f in xx??; do
>   path=$(grep -m1 '^#' $f | sed -r 's|#{1,} \`(.*)\`|\1|g;s|\.|/|g')
>   grep -v '^%%%' $f > "$path.md"  # double quotes are needed
>   rm $f
> done
```

Attributes
----------
TPL_CLASSDEF : string.Template
    Template to render `class` objects.
TPL_FUNCTIONDEF : string.Template
    Template to render `def` objects (async or not).
TPL_MODULE : string.Template
    Template to render the module summary.
TPL : string.Template
    Template to render the overall page (only governs order of objects in the output).
"""

import ast
import glob
import os
import re
import string
import sys
import typing

TPL_CLASSDEF = string.Template(
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

TPL_FUNCTIONDEF = string.Template(
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

TPL_MODULE = string.Template(
    "\n# Module `$module`\n\n$docstring\n\n$funcnames\n\n$classnames"
)

TPL = string.Template("$module\n\n$functions\n\n$classes")

# if requested, show private objects in the output
_show_private = (
    True
    if os.environ.get("ASTDOCS_SHOW_PRIVATE", "off") in ("1", "on", "true", "yes")
    else False
)

# if requested, split things up with %%% markers
_split_by = os.environ.get("ASTDOCS_SPLIT_BY", "m")
if "c" in _split_by:
    TPL_CLASSDEF.template = (
        f"%%%BEGIN CLASSDEF $ancestry.$classname{TPL_CLASSDEF.template}"
    )
if "f" in _split_by:
    TPL_FUNCTIONDEF.template = (
        f"%%%BEGIN FUNCTIONDEF $ancestry.$funcname{TPL_FUNCTIONDEF.template}"
    )
if "m" in _split_by:
    TPL_MODULE.template = f"%%%BEGIN MODULE $module{TPL_MODULE.template}"

# if requested, add the line numbers to the source
_with_linenos = os.environ.get("ASTDOCS_WITH_LINENOS", "off")
if _with_linenos not in ("1", "on", "true", "yes"):
    TPL_CLASSDEF.template = TPL_CLASSDEF.template.replace(
        "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
    )
    TPL_FUNCTIONDEF.template = TPL_FUNCTIONDEF.template.replace(
        "\n\n%%%SOURCE $path:$lineno:$endlineno", ""
    )

_classdefs = {}
_funcdefs = {}
_objects = {}


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

    Known problems
    --------------
    * Does not support `lambda` functions.
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

    # another complicate case: decorator with arguments
    if hasattr(a, "func"):
        s += format_annotation(a.func)
        s += f'({", ".join([format_annotation(a_) for a_ in a.args])}))'

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

    Notes
    -----
    If the regular expression solution presented here (which works for *my* needs) does
    not fulfill your standards, it is pretty easy to clobber it:

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

    Known problems
    --------------
    * Overall naive and *very* opinionated (again, for *my* use).
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

    # save the interesting details (more to come during rendering)
    _classdefs[f"{n.ancestry}.{n.name}"] = {
        "ancestry": n.ancestry,
        "classname": n.name,
        "classdocs": format_docstring(n),
        "decoration": "**Decoration:** via " + ", ".join(dc) + "." if dc else "",
        "endlineno": n.end_lineno,
        "hashtags": ht,
        "lineno": n.lineno,
    }

    # save the object
    _objects[n.name] = f"{n.ancestry}.{n.name}"


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

    # parse/format arguments and annotations
    params = [f'{a.arg}{format_annotation(a.annotation, ": ")}' for a in n.args.args]
    returns = format_annotation(n.returns, " -> ")

    # add line breaks if the function call is long (pre-render this latter first, no way
    # around it)
    rendered = len(f'{n.name}({", ".join(params)}){returns}')
    if rendered > os.environ.get("ASTDOCS_FOLD_ARGS_AFTER", 88):
        params = [f"\n    {p}" for p in params]
        suffix = "\n"
    else:
        suffix = ""

    # save the interesting details
    _funcdefs[f"{n.ancestry}.{n.name}"] = {
        "ancestry": n.ancestry,
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
    _objects[n.name] = f"{n.ancestry}.{n.name}"


def parse_import(n: typing.Union[ast.Import, ast.ImportFrom]):
    """Parse `import ... [as ...]` and `from ... import ... [as ...]` statements.

    The content built by this function is currently *not* used. This latter is kept in
    case all the objects (and aliases) accessible within a module is required for a
    post-processing or some later smart implementations.

    Parameters
    ----------
    n : typing.Union[ast.Import, ast.ImportFrom]
        The node to extract information from.
    """
    if hasattr(n, "module"):
        if n.module is None:
            path = ".".join(n.ancestry.split(".")[:-1])
        else:
            path = n.module
    else:
        path = ""

        for i in n.names:
            if i.asname is not None:
                objct = i.asname
            else:
                objct = i.name

        # save the object
        _objects[objct] = f"{path}.{i.name}".lstrip(".")


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


def postrender(func: typing.Callable) -> str:
    """Apply a post-rendering function on the output of the decorated function.

    This can be used to streamline the linting of the output, or immediately convert to
    `HTML` for instance.

    Parameters
    ----------
    func : typing.Callable
        The function to apply; should take a `str` as lone input.

    Returns
    -------
    : str
        `Markdown`-formatted content.

    Example
    -------

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
        return astodcs.render(filepath)

    print(render(...))
    ```
    """

    def decorator(f):
        def wrapper(*args, **kwargs):
            return func(f(*args, **kwargs))

        return wrapper

    return decorator


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
        f = _funcdefs.pop(init)
        params = f["params"]
        docstr = f["funcdocs"]
        lineno = f["lineno"]
        endlineno = f["endlineno"]
        if _with_linenos in ("1", "on", "true", "yes"):
            docstr += f"\n\n%%%SOURCE {filepath}:{lineno}:{endlineno}"
    else:
        params = ""
        docstr = ""

    # render all methods
    fr = []
    for f in fn:
        n = f.split(".")[-1]
        if not n.startswith("_") or _show_private:
            _funcdefs[f].update({"hashtags": f"{ht}##"})
            fr.append(render_functiondef(filepath, f))

    # methods bullet list
    for i, f in enumerate(fn):
        n = f.split(".")[-1]
        if not n.startswith("_") or _show_private:
            link = f.replace(".", "").lower()  # github syntax
            fn[i] = f"* [`{n}()`](#{link})"

    # update the description of the object
    _classdefs[name].update(
        {
            "params": params,
            "constdocs": docstr,
            "funcdefs": (ht + "# Methods\n\n" + "\n\n".join(fr)) if fr else "",
            "funcnames": ("**Methods:**\n\n" + "\n".join(fn)) if fn else "",
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
            if not n.startswith("_") or _show_private:
                link = f.replace(".", "").lower()  # github syntax
                fn.append(f"* [`{n}()`](#{link})")

    # classes bullet list
    cn = []
    for c in _classdefs:
        if c.count(".") == name.count(".") + 1:
            n = c.split(".")[-1]
            if not n.startswith("_") or _show_private:
                link = c.replace(".", "").lower()  # github syntax
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
    global _objects

    # make sure to flush the [global] objects in case multiple are rendered
    # it could be interesting to keep track of all objects over a whole package
    _classdefs = {}
    _funcdefs = {}
    _objects = {}

    with open(filepath) as f:

        # module ancestry
        m = filepath
        if remove_from_path:
            m = m.replace(remove_from_path, "")
        m = m.replace("/", ".").replace(".py", "")

        # traverse the ast
        n = ast.parse(f.read())
        n.name = m.replace(".__init__", "")
        parse_tree(n)

    # only the objects at the root of the module
    fr = []
    for f in _funcdefs:
        if f.count(".") == n.name.count(".") + 1:
            name = f.split(".")[-1]
            if not name.startswith("_") or _show_private:
                fr.append(render_functiondef(filepath, f))

    cr = []
    for c in _classdefs:
        if c.count(".") == n.name.count(".") + 1:
            name = c.split(".")[-1]
            if not name.startswith("_") or _show_private:
                cr.append(render_classdef(filepath, c))

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
        "module": render_module(n.name, format_docstring(n)),
    }

    s = TPL.substitute(sub).strip()

    # cleanup (extra line breaks)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"\n{2,}%%%BEGIN", "\n%%%BEGIN", s)

    return s


def render_recursively(path: str, remove_from_path: str = "") -> str:
    """Run pipeline on each `Python` module found in a folder and its subfolders.

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
    """
    mr = []

    # render each module
    for filepath in sorted(glob.glob(f"{path}/**/*.py", recursive=True)):
        name = filepath.split("/")[-1]
        if not name.startswith("_") or _show_private:
            mr.append(render(filepath, remove_from_path))

    s = "\n\n".join(mr)

    # cleanup (extra line breaks)
    s = re.sub(r"\n{2,}%%%BEGIN", "\n%%%BEGIN", s)

    return s


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit(
            "Too many arguments!"
            f'Please read the docs via `pydoc {sys.argv[0].replace(".py", "")}` or so.'
        )

    try:
        md = render(sys.argv[1])
    except IsADirectoryError:
        md = render_recursively(sys.argv[1])

    print(md)
