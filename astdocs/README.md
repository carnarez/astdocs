# Module `astdocs`

Extract and format documentation from `Python` code.

> **According to **my** standards.**

In a few more words, parse the underlying Abstract Syntax Tree (AST) description. (See
the [documentation](https://docs.python.org/3/library/ast.html) of the standard library
module with same name.) It expects a relatively clean input (demonstrated in this very
script) which forces *me* to keep *my* code somewhat correctly documented and without
fancy syntax.

My only requirement was to use the `Python` standard library **exclusively** (even the
[templating](https://docs.python.org/3/library/string.html#template-strings)) as it is
quite \[overly\] complete these days, and keep it as *lean* as possible. Support for
corner cases is scarse... for one, no class-in- nor function-in-function (which I
consider private, in the `Python` sense).

The simplest way to check the output of this script is to run it on itself:

```shell
$ python astdocs.py astdocs.py  # pipe it to your favourite markdown linter
```

or even:

```shell
$ python astdocs.py .  # recursively look for *.py files in the current directory
```

The behaviour of this little stunt can be modified via environment variables:

- `ASTDOCS_BOUND_OBJECTS` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored/counted as negative) to add `%%%START ...` and `%%%END ...` markers to
  indicate the beginning/end of an object (useful for further styling when rendering in
  `HTML` for example). **Not to be mixed up with the `%%%BEGIN` markers** (see below).
- `ASTDOCS_FOLD_ARGS_AFTER` to fold long object (function/method) definitions (many
  parameters). Defaults to 88 characters, [`black`](https://github.com/psf/black)
  [recommended](https://www.youtube.com/watch?v=wf-BqAjZb8M&t=260s&ab_channel=PyCon2015)
  default.
- `ASTDOCS_SHOW_PRIVATE` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored) to show `Python` private objects (which names start with an
  underscore).
- `ASTDOCS_SPLIT_BY` taking the `m`, `mc`, `mfc` or an empty value (default, all
  rendered content in one output): split each **m**odule, **f**unction and/or **c**lass
  (by adding `%%%BEGIN ...` markers). Classes will always keep their methods. In case
  `mfc` is provided, the module will only keep its docstring, and each
  function/class/method will be marked.
- `ASTDOCS_WITH_LINENOS` taking the `1`, `on`, `true` or `yes` values (anything else
  will be ignored) to show the line numbers of the object in the code source (to be
  processed later on by your favourite `Markdown` renderer). Look for the
  `%%%SOURCE ...` markers.

```shell
$ ASTDOCS_WITH_LINENOS=on python astdocs.py astdocs.py
```

or to split marked sections into separate files (in `Bash` below; see also the `Python`
example in the docstring of the `astdocs.render_recursively()` function):

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

Each of these environment variables translates into a private attribute with the same
name: the `ASTDOCS_FOLD_ARGS_AFTER` value is stored in the `_fold_args_after` variable
for instance.

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

**Attributes:**

- `TPL` \[`string.Template`\]: Template to render the overall page (only governs order
  of objects in the output).
- `TPL_CLASSDEF` \[`string.Template`\]: Template to render `class` objects.
- `TPL_FUNCTIONDEF` \[`string.Template`\]: Template to render `def` objects (async or
  not).
- `TPL_MODULE` \[`string.Template`\]: Template to render the module summary.

**Functions:**

- [`format_annotation()`](#astdocsformat_annotation)
- [`format_docstring()`](#astdocsformat_docstring)
- [`parse_classdef()`](#astdocsparse_classdef)
- [`parse_functiondef()`](#astdocsparse_functiondef)
- [`parse_import()`](#astdocsparse_import)
- [`parse_tree()`](#astdocsparse_tree)
- [`render_classdef()`](#astdocsrender_classdef)
- [`render_functiondef()`](#astdocsrender_functiondef)
- [`render_module()`](#astdocsrender_module)
- [`render()`](#astdocsrender)
- [`render_recursively()`](#astdocsrender_recursively)
- [`postrender()`](#astdocspostrender)
- [`main()`](#astdocsmain)

## Functions

### `astdocs.format_annotation`

```python
format_annotation(
    a: typing.Union[ast.Attribute, ast.Constant, ast.List, ast.Name, ast.Subscript], 
    char: str,
) -> str:
```

Format an annotation (object type or decorator).

Dive as deep as necessary within the children nodes until reaching the name of the
module/attribute objects are annotated after; save the import path on the way.
Recursively repeat for complicated object.

See the code itself for some line-by-line documentation.

**Parameters:**

- `a`
  \[`typing.Union[ast.Attribute, ast.Constant, ast.List, ast.Name, ast.Subscript]`\]:
  The starting node to extract annotation information from.
- `char` \[`str`\]: The additional character to place at the beginning of the
  annotation; `"@"` for a decorator, `" -> "` for a return type, *etc.* (defaults to
  empty string).

**Returns:**

- \[`str`\]: The formatted annotation.

**Known problems:**

- Does not support `lambda` functions.

### `astdocs.format_docstring`

```python
format_docstring(
    n: typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module],
) -> str:
```

Format the object docstring.

Expect some stiff `NumPy`-ish formatting (see
[this](https://numpydoc.readthedocs.io/en/latest/example.html#example) or
[that](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html)). Do
try to **type** all your input parameters/returned objects. And use a linter on the
output?

**Parameters:**

- `n`
  \[`typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module]`\]:
  Source node to extract/parse docstring from.

**Returns:**

- \[`str`\]: The formatted docstring.

**Example:**

Below the raw docstring example of what this very function is expecting as an input
(very inceptional):

```text
Parameters
----------
n : typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module]
    Source node to extract/parse docstring from.

Returns
-------
: str
    The formatted docstring.
```

The code blocks are extracted and replaced by placeholders before performing the
substitutions (then rolled back in). The regular expressions are then applied:

- Leading hashtags (`#`) are removed from any lines starting with them as we do not want
  to conflict with the `Markdown` output.
- Any series of words followed by a line with 3 or more hyphens is assumed to be a
  section marker (such as `Parameters`, `Returns`, `Example`, *etc.*).
- Lines with `parameter : type` (`: type` optional) followed by a description, itself
  preceded by four spaces are formatted as input parameters.
- Lines with `: type` (providing a type is here *mandatory*) followed by a description,
  itself preceded by four spaces are formatted as returned values.

Keep in mind that returning **the full path** to a returned object is always preferable.
And indeed **some of it could be inferred** from the function call itself, or the
`return` statement. BUT this whole thing is to force *myself* to structure *my*
docstrings correctly.

**Notes:**

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

**Known problems:**

- Overall naive and *very* opinionated (again, for *my* use).
- Does not support list in parameter/return entries.

### `astdocs.parse_classdef`

```python
parse_classdef(n: ast.ClassDef):
```

Parse a `class` statement.

**Parameters:**

- `n` \[`ast.ClassDef`\]: The node to extract information from.

### `astdocs.parse_functiondef`

```python
parse_functiondef(n: typing.Union[ast.AsyncFunctionDef, ast.FunctionDef]):
```

Parse a `def` statement.

**Parameters:**

- `n` \[`typing.Union[ast.AsyncFunctionDef, ast.FunctionDef]`\]: The node to extract
  information from.

### `astdocs.parse_import`

```python
parse_import(n: typing.Union[ast.Import, ast.ImportFrom]):
```

Parse `import ... [as ...]` and `from ... import ... [as ...]` statements.

The content built by this function is currently *not* used. This latter is kept in case
all the objects (and aliases) accessible within a module is required for a
post-processing or some later smart implementations.

**Parameters:**

- `n` \[`typing.Union[ast.Import, ast.ImportFrom]`\]: The node to extract information
  from.

### `astdocs.parse_tree`

```python
parse_tree(n: typing.Any):
```

Recursively traverse the nodes of the abstract syntax tree.

The present function calls the formatting function corresponding to the node name (if
supported) to parse/format it.

Add an `.ancestry` attribute on each traversed children object containing the complete
path to that object. This path is used to identify ownership of objects (function *vs.*
method for instance).

**Parameters:**

- \[`n`\]: Any type of node to extract information from.

### `astdocs.render_classdef`

```python
render_classdef(filepath: str, name: str) -> str:
```

Render a `class` object, according to the defined `TPL_CLASSDEF` template.

**Parameters:**

- `filepath` \[`str`\]: Path to the module (file) defining the object.
- `name` \[`str`\]: The name (full path including all ancestors) of the object to
  render.

**Returns:**

- \[`str`\]: `Markdown`-formatted description of the class object.

### `astdocs.render_functiondef`

```python
render_functiondef(filepath: str, name: str) -> str:
```

Render a `def` object (function or method).

Follow the defined `TPL_FUNCTIONDEF` template.

**Parameters:**

- `filepath` \[`str`\]: Path to the module (file) defining the object.
- `name` \[`str`\]: The name (full path including all ancestors) of the object to
  render.

**Returns:**

- \[`str`\]: `Markdown`-formatted description of the function/method object.

### `astdocs.render_module`

```python
render_module(name: str, docstring: str) -> str:
```

Render a module summary as a `Markdown` file.

Follow the defined `TPL_MODULE` template.

**Parameters:**

- `name` \[`str`\]: Name of the module being parsed.
- `docstring` \[`str`\]: The docstring of the module itself, if present (defaults to an
  empty string).

**Returns:**

- \[`str`\]: `Markdown`-formatted description of the whole module.

### `astdocs.render`

```python
render(filepath: str, remove_from_path: str) -> str:
```

Run the whole pipeline (useful wrapper function when this gets used as a module).

**Parameters:**

- `filepath` \[`str`\]: The path to the module to process.
- `remove_from_path` \[`str`\]: Part of the path to be removed. If one is rendering the
  content of a file buried deep down in a complicated folder tree *but* does not want
  this to appear in the ancestry of the module.

**Returns:**

- \[`str`\]: `Markdown`-formatted content.

### `astdocs.render_recursively`

```python
render_recursively(path: str, remove_from_path: str) -> str:
```

Run pipeline on each `Python` module found in a folder and its subfolders.

**Parameters:**

- `path` \[`str`\]: The path to the folder to process.
- `remove_from_path` \[`str`\]: Part of the path to be removed.

**Returns:**

- \[`str`\]: `Markdown`-formatted content for all `Python` modules within the path.

**Example:**

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

### `astdocs.postrender`

```python
postrender(func: typing.Callable):
```

Apply a post-rendering function on the output of the decorated function.

This can be used to streamline the linting of the output, or immediately convert to
`HTML` for instance.

**Parameters:**

- `func` \[`typing.Callable`\]: The function to apply; should take a `str` as lone
  input, the `Markdown` to process.

**Returns:**

- \[`str`\]: `Markdown`-formatted content.

**Example:**

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

### `astdocs.main`

```python
main():
```

Process CLI calls.
