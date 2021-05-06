# Module `astdocs`

Extract and format documentation from `Python` code.

*According to **my** standards.*

In a few more words, parse the underlying Abstract Syntax Tree (AST) description. (See
the [documentation](https://docs.python.org/3/library/ast.html) of the standard library
module with same name.) It expects a relatively clean input (demonstrated in this very
script) which forces me to keep my code somewhat correctly documented and without fancy
syntax.

My only requirement was to use the `Python` standard library **exclusively** (even the
[templating](https://docs.python.org/3/library/string.html#template-strings)) as it is
quite \[overly\] complete these day, and keep it as *lean* as possible. Support for
corner cases is scarse... for one, no class-in- nor function-in-function (which I
consider private, in the `Python` sense).

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

- `ASTDOCS_FOLD_ARGS_AFTER` to fold long object (function/method) definitions (many
  parameters). Defaults to 88 characters, [`black`](https://github.com/psf/black)
  [recommended](https://www.youtube.com/watch?v=wf-BqAjZb8M&t=260s&ab_channel=PyCon2015)
  default.
- `ASTDOCS_SHOW_PRIVATE` taking the `1`, `on`, `true` or `yes` values (anything else will
  be ignored/counted as negative) to show `Python` private objects (which names start with
  an underscore).
- `ASTDOCS_SPLIT_BY` taking the `m`, `mc`, `mfc` or an empty value (default, all rendered
  content in one output): split each **m**odule, **f**unction and/or **c**lass (by adding
  `%%%BEGIN ...` markers). Classes will always keep their methods. In case `mfc` is
  provided, the module will only keep its docstring, and each function will be marked.
- `ASTDOCS_WITH_LINENOS` taking the `1`, `on`, `true` or `yes` values (anything else will
  be ignored) to show the line numbers of the object in the code source (to be processed
  later on by your favourite `Markdown` renderer). Look for the `%%%SOURCE` markers.

```shell
$ ASTDOCS_WITH_LINENOS=on python astdocs.py astdocs.py
```

or to split marked sections into separate files (in `bash` below; see also the `Python`
example in the docstring of the `astdocs.render_recursively()` function):

```shell
$ ASTDOCS_SPLIT_BY=mc python astdocs.py module.py | csplit -qz - '/%%%BEGIN/' '{*}'
$ mv xx00 module.md
$ mkdir module
$ for f in xx??; do
>   path=$(grep -m1 '^%%%BEGIN' $f | sed -r 's|%%%[.*] [.*] (.*)|\1|g;s|\.|/|g')
>   mkdir -p $(dirname $path)
>   grep -v '^%%%BEGIN' $f > "$path.md"  # double quotes are needed
>   rm $f
> done
```

**Attributes:**

- `TPL_CLASSDEF` \[`string.Template`\]: Template to render `class` objects.
- `TPL_FUNCTIONDEF` \[`string.Template`\]: Template to render `def` objects (async or
  not).
- `TPL_MODULE` \[`string.Template`\]: Template to render the module summary.
- `TPL` \[`string.Template`\]: Template to render the overall page (only governs order of
  objects in the output).

**Functions:**

- [`format_annotation()`](#astdocsformat_annotation)
- [`format_docstring()`](#astdocsformat_docstring)
- [`parse_classdef()`](#astdocsparse_classdef)
- [`parse_functiondef()`](#astdocsparse_functiondef)
- [`parse_import()`](#astdocsparse_import)
- [`parse_tree()`](#astdocsparse_tree)
- [`postrender()`](#astdocspostrender)
- [`render_classdef()`](#astdocsrender_classdef)
- [`render_functiondef()`](#astdocsrender_functiondef)
- [`render_module()`](#astdocsrender_module)
- [`render()`](#astdocsrender)
- [`render_recursively()`](#astdocsrender_recursively)

## Functions

### `astdocs.format_annotation`

```python
format_annotation(a: typing.Union[ast.Attribute, ast.Name], char: str) -> str:
```

Format an annotation (object type or decorator).

Dive as deep as necessary within the children nodes until reaching the name of the
module/attribute objects are annotated after; save the import path on the way.
Recursively repeat for complicated object.

See the code itself for some line-by-line documentation.

**Parameters:**

- `a` \[`typing.Union[ast.Attribute, ast.Name]`\]: The starting node to extract annotation
  information from.
- `char` \[`str`\]: The additional character to place at the beginning of the annotation;
  `"@"` for a decorator, `" -> "` for a return type, *etc.* (defaults to empty string).

**Returns:**

- \[`str`\]: The formatted annotation.

**Known problems:**

- Does not support `lambda` functions.

### `astdocs.format_docstring`

```python
format_docstring(
    n: typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module]
) -> str:
```

Format the object docstring.

Expect some stiff `NumPy`-ish formatting (see
[this](https://numpydoc.readthedocs.io/en/latest/example.html#example) or
[that](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html)). Do
try to **type** all your input parameters/returned objects. And use a linter on the
output.

**Parameters:**

- `n` \[`typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module]`\]:
  Source node to extract/parse docstring from.

**Returns:**

- \[`str`\]: The formatted docstring.

**Notes:**

If the regular expression solution presented here (which works for *my* needs) does not
fulfill your standards, it is pretty easy to clobber it:

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

### `astdocs.postrender`

```python
postrender(func: typing.Callable) -> str:
```

Apply a post-rendering function on the output of the decorated function.

This can be used to streamline the linting of the output, or immediately convert to
`HTML` for instance.

**Parameters:**

- `func` \[`typing.Callable`\]: The function to apply; should take a `str` as lone input.

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
    return astodcs.render(filepath)

print(render(...))
```

### `astdocs.render_classdef`

```python
render_classdef(filepath: str, name: str) -> str:
```

Render a `class` object, according to the defined `TPL_CLASSDEF` template.

**Parameters:**

- `filepath` \[`str`\]: Path to the module (file) defining the object.
- `name` \[`str`\]: The name (full path including all ancestors) of the object to render.

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
- `name` \[`str`\]: The name (full path including all ancestors) of the object to render.

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
  content of a file buried deep down in a complicated folder tree *but* does not want this
  to appear in the ancestry of the module.

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

for line in astdocs.render_recursively(...).split("\n"):
    if line.startswith("%%%BEGIN"):
        try:
            output.close()
        except NameError:
            pass
        filepath = f'{line.split()[2].replace(".", "/")}.md'
        folder = "/".join(filepath.split("/")[:-1])
        os.makedirs(folder, exist_ok=True)
        output = open(filepath, "w")
    else:
        output.write(f"{line}\n")
output.close()
```
