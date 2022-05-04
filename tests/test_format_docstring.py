"""All tests related to the `astdocs.format_docstring()` function."""

import ast

from astdocs import format_docstring


def test_simple_class_docstring():
    '''Test extraction of simple docstring from a class definition.

    ```
    class Classy:
        """Test simple docstring."""
    ```
    '''
    s = "Test simple docstring."

    n = ast.parse(f'class Classy:\n    """{s}"""').body[0]
    assert format_docstring(n) == s


def test_simple_function_docstring():
    '''Test extration of simple docstring from [async] function definitions.

    ```
    def func():
        """Test simple docstring."""
    ```
    '''
    s = "Test simple docstring."

    # create the ast node (cumbersome...)
    n = ast.FunctionDef(
        name="func",
        args=ast.arguments(
            posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
        ),
        body=[ast.Expr(value=ast.Constant(value=s))],
        decorator_list=[],
    )

    assert format_docstring(n) == s

    # parse node from string: returns a module, first (sole) element being the function
    n = ast.parse(f'def func():\n    """{s}"""').body[0]
    assert format_docstring(n) == s

    n = ast.parse(f'async def func():\n    """{s}"""').body[0]
    assert format_docstring(n) == s


def test_simple_module_docstring():
    '''Test extraction of simple docstring from a module definition.

    ```
    """Test simple docstring."""

    def func():
        pass
    ```
    '''
    s = "Test simple docstring."

    n = ast.parse(f'"""{s}"""\n\ndef func():\n    pass')
    assert format_docstring(n) == s


def test_complex_docstring():
    '''Test extraction of more complex docstring (from module to make it easier).

    ````
    """Empty module.

    ## Cleaned up title

    ```python
    import astdocs
    ```

    ````text
    Let's test this too:
    ```markdown
    # Title
    ```
    ````

    Attributes
    ----------
    n : ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
        An `ast` node.
    m : int
        Number of things.
    self
        This module.

    Raises
    ------
    : Exception
        All kinds of exceptions

    """
    ````

    Notes
    -----
    * Docstring fetching.
    * Code blocks handling (with various number of backticks).
    * `Markdown` titles cleaning.
    * Categories (followed by `---` lines) parsing.
    * Argument + type + description parsing.
    * Argument + description parsing.
    * Type + description parsing.
    * Trailing spaces trimming.
    '''
    # even more cumbersome...
    docstring = "\n".join(
        [
            '"""Empty module.',
            "",
            "## Cleaned up title",
            "",
            "```python",
            "import astdocs",
            "```",
            "",
            "````text",
            "Let's test this too:",
            "```markdown",
            "# Title",
            "```",
            "````",
            "",
            "Attributes",
            "----------",
            "n : ast.ClassDef | ast.FunctionDef | ast.Module",
            "    An `ast` node.",
            "m : int",
            "    Number of things.",
            "self",
            "    This module.",
            "",
            "Raises",
            "------",
            ": Exception",
            "    All kinds of exceptions.",
            "",
            "",
            '"""',
        ]
    )

    # oof
    formatted = "\n".join(
        [
            "Empty module.",
            "",
            "**Cleaned up title**",
            "",
            "```python",
            "import astdocs",
            "```",
            "",
            "````text",
            "Let's test this too:",
            "```markdown",
            "# Title",
            "```",
            "````",
            "",
            "**Attributes**",
            "",
            "* `n` [`ast.ClassDef | ast.FunctionDef | ast.Module`]: An `ast` node.",
            "* `m` [`int`]: Number of things.",
            "* `self`: This module.",
            "",
            "**Raises**",
            "",
            "* [`Exception`]: All kinds of exceptions.",
        ]
    )

    n = ast.parse(docstring)
    assert format_docstring(n) == formatted
