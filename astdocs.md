# Module `astdocs`

Extract and format documentation from `Python` code.

In more details, parse the underlying Abstract Syntax Tree (AST) description. (See
[documentation](https://docs.python.org/3/library/ast.html) of the standard library
module with same name.)

The only requirement is to use the standard library **exclusively** (even the
[templating](https://docs.python.org/3/library/string.html#template-strings)), and keep
it as lean as possible. Support for corner cases is scarse... for one, no
class-in-function (or the opposite) or function-in-function.

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

- `ASTDOCS_FOLD_ARGS_AFTER` to fold long object (function/method) definition (many
  parameters). Defaults to 3.
- `ASTDOCS_SPLIT_BY` taking the `m` (default), `mc` or `mfc`: split each \[m\]odule,
  \[f\]unction and \[c\]lass apart (by adding `%%%BX` markers in the output, `X` being
  either `F` -functions/methods- or `C` -classes). Classes will always keep their methods.
  In case `mfc` is provided, the module will only keep its docstring, and each function
  will be marked.
- `ASTDOCS_WITH_LINENOS` taking the `1`, `on`, `true` or `yes` values (anything else will
  be ignored) to show the line numbers of the object in the code source (to be processed
  later on by your favourite `Markdown` renderer). Look for a `%%%SOURCE` marker.

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

print(astdocs.render(filepath))
```

**Attributes:**

- `CLASSDEF_TPL` \[`string.Template`\]: Template to render `class` objects.
- `FUNCTIONDEF_TPL` \[`string.Template`\]: Template to render `def` objects (async or
  not).
- `SUMMARY_TPL` \[`string.Template`\]: Template to render the module summary.
- `TPL` \[`string.Template`\]: Template to render the overall page (currently only governs
  order of objects)

**Functions:**

- [`format_annotation()`](#astdocsformat_annotation)
- [`format_docstring()`](#astdocsformat_docstring)
- [`parse_classdef()`](#astdocsparse_classdef)
- [`parse_functiondef()`](#astdocsparse_functiondef)
- [`parse_tree()`](#astdocsparse_tree)
- [`render_classdef()`](#astdocsrender_classdef)
- [`render_functiondef()`](#astdocsrender_functiondef)
- [`render_summary()`](#astdocsrender_summary)
- [`render()`](#astdocsrender)

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

### `astdocs.format_docstring`

```python
format_docstring(n: typing.Union[ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module]) -> str:
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

**Known problems:**

- Overall naive and *very* opinionated (for my use).
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

Render a `class` object, according to the defined `CLASSDEF_TPL` template.

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

Follow the defined `FUNCTIONDEF_TPL` template.

**Parameters:**

- `filepath` \[`str`\]: Path to the module (file) defining the object.
- `name` \[`str`\]: The name (full path including all ancestors) of the object to render.

**Returns:**

- \[`str`\]: `Markdown`-formatted description of the function/method object.

### `astdocs.render_summary`

```python
render_summary(name: str, docstring: str) -> str:
```

Render a module summary as a `Markdown` file.

Follow the defined `SUMMARY_TPL` template.

**Parameters:**

- `name` \[`str`\]: Name of the module being parsed.
- `docstring` \[`str`\]: The docstring of the module itself, if present (defaults to an
  empty string).

**Returns:**

- \[`str`\]: `Markdown`-formatted description of the whole module.

### `astdocs.render`

```python
render(filepath: str) -> str:
```

Run the whole pipeline (wrapper method).

**Parameters:**

- `filepath` \[`str`\]: The path to the module to process.

**Returns:**

- \[`str`\]: `Markdown`-formatted content.
