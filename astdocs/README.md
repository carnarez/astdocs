# Module `astdocs`

Extract and format `Markdown` documentation from `Python` code.

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

**Attributes**

* `TPL` [`string.Template`]: Template to render the overall page (only governs order of objects in the output).
* `TPL_CLASSDEF` [`string.Template`]: Template to render `class` objects.
* `TPL_FUNCTIONDEF` [`string.Template`]: Template to render `def` objects (async or not).
* `TPL_MODULE` [`string.Template`]: Template to render the module summary.
* `objects` [`dict[str, typing.Any]`]: Nested dictionary of all relevant objects encountered while parsing the source code.

**Functions**

* [`format_docstring()`](#astdocsformat_docstring): Format the object docstring.
* [`parse_annotation()`](#astdocsparse_annotation): Format an annotation (object type or decorator).
* [`parse_class()`](#astdocsparse_class): Parse a `class` statement.
* [`parse_function()`](#astdocsparse_function): Parse a `def` statement.
* [`parse_import()`](#astdocsparse_import): Parse `import ... [as ...]` and `from ... import ... [as ...]` statements.
* [`parse()`](#astdocsparse): Recursively traverse the nodes of the abstract syntax tree.
* [`render_class()`](#astdocsrender_class): Render a `class` object, according to the defined `TPL_CLASSDEF` template.
* [`render_function()`](#astdocsrender_function): Render a `def` object (function or method).
* [`render_module()`](#astdocsrender_module): Render a module summary as a `Markdown` file.
* [`render()`](#astdocsrender): Run the whole pipeline (useful wrapper function when this gets used as a module).
* [`render_recursively()`](#astdocsrender_recursively): Run pipeline on each `Python` module found in a folder and its subfolders.
* [`postrender()`](#astdocspostrender): Apply a post-rendering function on the output of the decorated function.
* [`cli()`](#astdocscli): Process CLI calls.

## Functions

### `astdocs.format_docstring`

```python
format_docstring(
    node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module,
) -> str:
```

Format the object docstring.

Expect some stiff `NumPy`-ish formatting (see
[this](https://numpydoc.readthedocs.io/en/latest/example.html#example) or
[that](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html)).
Do try to **type** all your input parameters/returned objects. And use a linter on
the output?

**Parameters**

* `node` [`ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module`]: Source node to extract/parse docstring from.

**Returns**

* [`str`]: The formatted docstring.

**Example**

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

**Notes**

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

**Known problem**

Overall naive, stiff and *very* opinionated (again, for *my* use).

### `astdocs.parse_annotation`

```python
parse_annotation(a: typing.Any) -> str:
```

Format an annotation (object type or decorator).

Dive as deep as necessary within the children nodes until reaching the name of the
module/attribute objects are annotated after; save the import path on the way.
Recursively repeat for complicated object.

See the code itself for some line-by-line documentation.

**Parameters**

* `a` [`typing.Any`]: The starting node to extract annotation information from.

**Returns**

* [`str`]: The formatted annotation.

**Known problems**

* The implementation only supports nodes I encountered in my projects.
* Does not support `lambda` constructs.

### `astdocs.parse_class`

```python
parse_class(
    node: ast.ClassDef,
    module: str,
    ancestry: str,
    classes: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
```

Parse a `class` statement.

**Parameters**

* `node` [`ast.ClassDef`]: The node to extract information from.
* `module` [`str`]: Name of the current module.
* `ancestry` [`str`]: Complete path to the object, used to identify ownership of children objects
    (functions and methods for instance).
* `classes` [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered class definitions.

**Returns**

* [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered class definitions.

### `astdocs.parse_function`

```python
parse_function(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
    module: str,
    ancestry: str,
    functions: dict[str, dict[str, str]],
) -> dict[str, dict]:
```

Parse a `def` statement.

**Parameters**

* `node` [`ast.AsyncFunctionDef | ast.FunctionDef`]: The node to extract information from.
* `module` [`str`]: Name of the current module.
* `ancestry` [`str`]: Complete path to the object, used to identify ownership of children objects
    (functions and methods for instance).
* `functions` [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered function definitions.

**Returns**

* [`dict[str, dict]`]: Dictionnaries of all encountered function definitions.

**Notes**

If `*args` and some `kwargs` arguments are present, `args.vararg` will not be `None`
and the `node.args.kwonlyargs` / `node.args.kw_defaults` attributes need to be
parsed. Otherwise all should be available in the `args` / `defaults` attributes.

### `astdocs.parse_import`

```python
parse_import(
    node: ast.Import | ast.ImportFrom,
    module: str,
    ancestry: str,
    imports: dict[str, str],
) -> dict[str, str]:
```

Parse `import ... [as ...]` and `from ... import ... [as ...]` statements.

The content built by this function is currently *not* rendered. This latter is kept
in case all the objects (and aliases) accessible within a module is required for a
post-processing or some later [smart and exciting] implementations.

**Parameters**

* `node` [`ast.Import | ast.ImportFrom`]: The node to extract information from.
* `module` [`str`]: Name of the current module.
* `ancestry` [`str`]: Complete path to the object, used to identify ownership of children objects
    (functions and methods for instance).
* `imports` [`dict[str, str] | None`]: Dictionnaries of parsed imports. Defaults to an empty dictionnary `{}`.

**Returns**

* [`dict[str, str]`]: Dictionnaries of all encountered imports. Untouched for now, always empty
    dictionnary `{}`.

### `astdocs.parse`

```python
parse(
    node: typing.Any,
    module: str,
    ancestry: str = "",
    classes: dict[str, dict[str, str]] | None = None,
    functions: dict[str, dict[str, str]] | None = None,
    imports: dict[str, str] | None = None,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, str]]:
```

Recursively traverse the nodes of the abstract syntax tree.

The present function calls the formatting function corresponding to the node name
(if supported) to parse/format it.

**Parameters**

* `node` [`typing.Any`]: Any type of node to extract information from.
* `module` [`str`]: Name of the current module.
* `ancestry` [`str`]: Complete path to the object, used to identify ownership of children objects
    (functions and methods for instance).
* `classes` [`dict[str, dict[str, str]] | None`]: Dictionnaries of parsed class definitions. Defaults to `None`.
* `functions` [`dict[str, dict[str, str]] | None`]: Dictionnaries of parsed function definitions. Defaults to `None`.
* `imports` [`dict[str, str] | None`]: Dictionnaries of parsed imports. Defaults to a `None`.

**Returns**

* [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered class definitions.
* [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered function definitions.
* [`dict[str, str]`]: Dictionnaries of all encountered imports.

### `astdocs.render_class`

```python
render_class(
    filepath: str,
    name: str,
    classes: dict[str, dict[str, str]],
    functions: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
) -> str:
```

Render a `class` object, according to the defined `TPL_CLASSDEF` template.

**Parameters**

* `filepath` [`str`]: Path to the module (file) defining the object.
* `name` [`str`]: The name (full path including all ancestors) of the object to render.
* `classes` [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered class definitions.
* `functions` [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered function definitions.
* `config` [`dict[str, typing.Any]`]: Configuration options used to render attributes.

**Returns**

* [`str`]: `Markdown`-formatted description of the class object.

### `astdocs.render_function`

```python
render_function(filepath: str, name: str, functions: dict[str, dict[str, str]]) -> str:
```

Render a `def` object (function or method).

Follow the defined `TPL_FUNCTIONDEF` template.

**Parameters**

* `filepath` [`str`]: Path to the module (file) defining the object.
* `name` [`str`]: The name (full path including all ancestors) of the object to render.
* `functions` [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered function definitions.

**Returns**

* [`str`]: `Markdown`-formatted description of the function/method object.

### `astdocs.render_module`

```python
render_module(
    name: str,
    docstring: str,
    classes: dict[str, dict[str, str]],
    functions: dict[str, dict[str, str]],
    config: dict[str, typing.Any] = config,
) -> str:
```

Render a module summary as a `Markdown` file.

Follow the defined `TPL_MODULE` template.

**Parameters**

* `name` [`str`]: Name of the module being parsed.
* `docstring` [`str`]: The docstring of the module itself, if present (defaults to an empty string).
* `classes` [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered class definitions.
* `functions` [`dict[str, dict[str, str]]`]: Dictionnaries of all encountered function definitions.
* `config` [`dict[str, typing.Any]`]: Configuration options used to render attributes.

**Returns**

* [`str`]: `Markdown`-formatted description of the whole module.

### `astdocs.render`

```python
render(
    filepath: str = "",
    remove_from_path: str = "",
    code: str = "",
    module: str = "",
    config: dict[str, typing.Any] = config,
) -> str:
```

Run the whole pipeline (useful wrapper function when this gets used as a module).

**Parameters**

* `filepath` [`str`]: The path to the module to process. Defaults to empty string.
* `remove_from_path` [`str`]: Part of the path to be removed. If one is rendering the content of a file buried
    deep down in a complicated folder tree *but* does not want this to appear in the
    ancestry of the module. Defaults to empty string.
* `code` [`str`]: Code to process; useful when used as a module. If both `filepath` and `code` are
    provided the latter will be ignored. Defaults to empty string.
* `module` [`str`]: Name of the current module. Defaults to empty string.
* `config` [`dict[str, typing.Any]`]: Configuration options used to render attributes.

**Returns**

* [`str`]: `Markdown`-formatted content.

### `astdocs.render_recursively`

```python
render_recursively(
    path: str,
    remove_from_path: str = "",
    config: dict[str, typing.Any] = config,
) -> str:
```

Run pipeline on each `Python` module found in a folder and its subfolders.

**Parameters**

* `path` [`str`]: The path to the folder to process.
* `remove_from_path` [`str`]: Part of the path to be removed.
* `config` [`dict[str, typing.Any]`]: Configuration options used to render attributes.

**Returns**

* [`str`]: `Markdown`-formatted content for all `Python` modules within the path.

**Example**

```python
import astdocs
import re

outdir = "docs"

for line in astdocs.render_recursively(...).split("\n"):
    if line.startswith("%%%BEGIN"):
        try:
            output.close()
        except NameError:
            pass
        path = re.sub(
            r"\.py$",
            ".md",
            "/".join([outdir.rstrip("/")] + line.split()[2].split(".")),
        )
        os.makedirs(path.split("/")[:-1], exist_ok=True)
        output = open(path, "w")
    else:
        output.write(f"{line}\n")
try:
    output.close()
except NameError:
    pass
```

### `astdocs.postrender`

```python
postrender(func: typing.Callable) -> typing.Callable:
```

Apply a post-rendering function on the output of the decorated function.

This can be used to streamline the linting of the output, or immediately convert to
`HTML` for instance.

**Parameters**

* `func` [`typing.Callable`]: The function to apply; should take a `str` as lone input, the `Markdown` to
    process.

**Returns**

* [`str`]: `Markdown`-formatted content.

**Example**

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

```python
import astdocs
import re

def extract_snippet(md: str) -> str:
    for m in re.finditer("^%%%SOURCE (.*):([0-9]+):([0-9]+)\n", md):
        ms = m.group(0)  # matched string
        fp, cs, ce = m.groups()  # path to module, first and last line of snippet
        with open(fp) as f:
            snippet = "\n".join(f.readlines()[cs:ce + 1])
        md = md.replace(
            ms, f"<details><summary>Source</summary>\n\n{snippet}\n\n</details>"
        )
    return md

@astdocs.postrender(extract_snippet)
def render(filepath: str) -> str:
    config = astdocs.config.copy()
    config.update({"with_linenos": True})
    return astdocs.render(filepath, config=config)

print(render(...))
```

### `astdocs.cli`

```python
cli() -> None:
```

Process CLI calls.
