# Module `test_cli`

Tests relate to the `cli()` function.

**Functions**

- [`test_runs()`](#test_clitest_runs): Test successful run (this test checks nothing
  more than a script run).
- [`test_faulty_run()`](#test_clitest_faulty_run): Test faulty run.
- [`test_environment()`](#test_clitest_environment): Test for environment variables.
- [`test_default_environment()`](#test_clitest_default_environment): Test for
  environment variables (reset them for the tests).

## Functions

### `test_cli.test_runs`

```python
test_runs():
```

Test successful run (this test checks nothing more than a script run).

### `test_cli.test_faulty_run`

```python
test_faulty_run():
```

Test faulty run.

### `test_cli.test_environment`

```python
test_environment():
```

Test for environment variables.

### `test_cli.test_default_environment`

```python
test_default_environment():
```

Test for environment variables (reset them for the tests).

# Module `test_format`

All tests related to the `astdocs.format_docstring()` function.

**Functions**

- [`test_simple_class_docstring()`](#test_formattest_simple_class_docstring): Test
  extraction of simple docstring from a class definition.
- [`test_simple_function_docstring()`](#test_formattest_simple_function_docstring): Test
  extration of simple docstring from \[async\] function definitions.
- [`test_simple_module_docstring()`](#test_formattest_simple_module_docstring): Test
  extraction of simple docstring from a module definition.
- [`test_complex_docstring()`](#test_formattest_complex_docstring): Test extraction of
  more complex docstring (from module to make it easier).

## Functions

### `test_format.test_simple_class_docstring`

```python
test_simple_class_docstring():
```

Test extraction of simple docstring from a class definition.

```
class Classy:
    """Test simple docstring."""
```

### `test_format.test_simple_function_docstring`

```python
test_simple_function_docstring():
```

Test extration of simple docstring from \[async\] function definitions.

```
def func():
    """Test simple docstring."""
```

### `test_format.test_simple_module_docstring`

```python
test_simple_module_docstring():
```

Test extraction of simple docstring from a module definition.

```
"""Test simple docstring."""

def func():
    pass
```

### `test_format.test_complex_docstring`

```python
test_complex_docstring():
```

Test extraction of more complex docstring (from module to make it easier).

`````
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
`````

**Notes**

- Docstring fetching.
- Code blocks handling (with various number of backticks).
- `Markdown` titles cleaning.
- Categories (followed by `---` lines) parsing.
- Argument + type + description parsing.
- Argument + description parsing.
- Type + description parsing.
- Trailing spaces trimming.

# Module `test_parse`

All tests related to the `astdocs.parse_*()` function.

**Functions**

- [`test_simple_decorator()`](#test_parsetest_simple_decorator): Test for decoration
  parsing.
- [`test_complex_decorator()`](#test_parsetest_complex_decorator): Test for more
  complicated decoration.
- [`test_inheritance()`](#test_parsetest_inheritance): Test for multiple inheritance.
- [`test_simple_parameters_typing()`](#test_parsetest_simple_parameters_typing): Test
  for simple input/output arguments.
- [`test_simple_parameters_v310()`](#test_parsetest_simple_parameters_v310): Test for
  simple input/output arguments (v3.10 syntax).
- [`test_with_args_kwargs()`](#test_parsetest_with_args_kwargs): Test for presence of
  `*args` and `**kwargs` in function arguments (v3.10 syntax).
- [`test_complex_parameters_typing()`](#test_parsetest_complex_parameters_typing): Test
  for complex input/output arguments.
- [`test_complex_parameters_v310()`](#test_parsetest_complex_parameters_v310): Test for
  complex input/output arguments (v3.10 syntax).
- [`test_class()`](#test_parsetest_class): Test for class including `__init__` and
  methods.
- [`test_function()`](#test_parsetest_function): Test for a simple function.
- [`test_import()`](#test_parsetest_import): Test for a simple function.

## Functions

### `test_parse.test_simple_decorator`

```python
test_simple_decorator():
```

Test for decoration parsing.

```python
@decorator
class Classy:
    """Docstring"""
```

```python
@first
@second
def func():
    pass
```

### `test_parse.test_complex_decorator`

```python
test_complex_decorator():
```

Test for more complicated decoration.

```python
@decorator(including=parameter, and_with=another)
def func():
    pass
```

### `test_parse.test_inheritance`

```python
test_inheritance():
```

Test for multiple inheritance.

```python
import inlaws
import foreign.family

class Class(Parent, inlaws.Parent, foreign.family.Parent):
    """Docstring"""
```

### `test_parse.test_simple_parameters_typing`

```python
test_simple_parameters_typing():
```

Test for simple input/output arguments.

```python
import typing

def func(a, b: typing.Union[bool, str] = None, c: int = 0) -> str:
    return str(j)
```

### `test_parse.test_simple_parameters_v310`

```python
test_simple_parameters_v310():
```

Test for simple input/output arguments (v3.10 syntax).

```python
def func(a, b: bool | float | str, c: int = 0) -> str:
    return str(j)
```

### `test_parse.test_with_args_kwargs`

```python
test_with_args_kwargs():
```

Test for presence of `*args` and `**kwargs` in function arguments (v3.10 syntax).

```python
def func(a, *args, b: list[bool] = [True, False], **kwargs):
    pass
```

### `test_parse.test_complex_parameters_typing`

```python
test_complex_parameters_typing():
```

Test for complex input/output arguments.

```python
import typing
import package.module.submodule

def func(
    a: typing.Tuple[int, str],
    b: typing.List[typing.Union[int, str]],
    c: typing.Dict[str, typing.Any],
    d: typing.Set[float],
    e: package.module.submodule.Object,
):
    pass
```

### `test_parse.test_complex_parameters_v310`

```python
test_complex_parameters_v310():
```

Test for complex input/output arguments (v3.10 syntax).

```python
from typing import Any
import package.module.submodule

def func(
    a: tuple[int, str] = (0, "test"),
    b: list[int | str] = [0, "test"],
    c: dict[str, Any] = {"0": True},
    d: set[float] = {0.0, 1.0, 2.0},
):
    pass
```

### `test_parse.test_class`

```python
test_class():
```

Test for class including `__init__` and methods.

```python
class Classy:

    def __init__(self, a: str, b: list[bool], **kwargs):
        pass

    @staticmethod
    def static_method(i: int):
        pass

    def method(self, j: str):
        pass
```

### `test_parse.test_function`

```python
test_function():
```

Test for a simple function.

```python
def func(a, b: bool | float | str = "", c: int = 0) -> str:
    return str(j)
```

### `test_parse.test_import`

```python
test_import():
```

Test for a simple function.

```python
import module
import module1, module2, module3
import package.module
import package.module.submodule as alias
from .. import *
from .module import Object, function
from module.submodule import AnotherObject as ThatObject
from package.module.submodule import YetAnotherObject as short_alias
```

# Module `test_render`

All tests related to the `astdocs.render_*()` functions.

**Functions**

- [`test_empty()`](#test_rendertest_empty): Test for no input (just to get 100%
  coverage).
- [`test_remove_from_path()`](#test_rendertest_remove_from_path): Test with the
  `remove_from_path` argument (just to get 100% coverage).
- [`test_simple_class()`](#test_rendertest_simple_class): Test for simple class
  rendering.
- [`test_complex_class()`](#test_rendertest_complex_class): Test for class including
  `__init__` and methods.
- [`test_complex_function()`](#test_rendertest_complex_function): Test for complex
  input/output arguments.
- [`test_private_hidden_objects()`](#test_rendertest_private_hidden_objects): Test for
  private objects.
- [`test_private_visible_objects()`](#test_rendertest_private_visible_objects): Test for
  visible private objects.
- [`test_it_all()`](#test_rendertest_it_all): Test for a full example (concatention of
  other snippets).
- [`test_postrender_decorator()`](#test_rendertest_postrender_decorator): Test the
  output of the `@postrender` decorator.
- [`test_alternate_config()`](#test_rendertest_alternate_config): Test for different
  configuration options.

## Functions

### `test_render.test_empty`

```python
test_empty():
```

Test for no input (just to get 100% coverage).

### `test_render.test_remove_from_path`

```python
test_remove_from_path():
```

Test with the `remove_from_path` argument (just to get 100% coverage).

This test checks literally *nothing* more than the `remove_from_path` flag of the
`render()` function. Return is ignored.

### `test_render.test_simple_class`

```python
test_simple_class():
```

Test for simple class rendering.

```python
class Classy:
    """A classy class."""

    def method(self, i: str):
        """Methodically classy."""
```

### `test_render.test_complex_class`

```python
test_complex_class():
```

Test for class including `__init__` and methods.

```python
@decorator
class Classy(Parent):
    """A classy class."""

    def __init__(self, a: str, b: list[bool], *args, **kwargs):
        """Initialize the object."""

    @staticmethod
    def static_method(i: int):
        """Statically classy."""

    def method(self, j: str):
        pass
```

### `test_render.test_complex_function`

```python
test_complex_function():
```

Test for complex input/output arguments.

```python
from typing import Any

@decorator
def func(
    *args,
    a: tuple[int, str] = (0, "test"),
    b: list[int | str] = [0, "test"],
    c: dict[str, Any] = {"0": True},
    d: set[float] = {0.0, 1.0, 2.0},
    **kwargs,
):
    """Do this and that."""

def _hidden():
    pass
```

### `test_render.test_private_hidden_objects`

```python
test_private_hidden_objects():
```

Test for private objects.

```python
def _hidden():
    """Am hiding."""

class _Hidden:
    """Am hiding."""
```

### `test_render.test_private_visible_objects`

```python
test_private_visible_objects():
```

Test for visible private objects.

```python
def _hidden():
    """Am hiding."""

class _Hidden:
    """Am hiding."""
```

### `test_render.test_it_all`

```python
test_it_all():
```

Test for a full example (concatention of other snippets).

```python
from typing import Any

@decorator
def func(
    *args,
    a: tuple[int, str] = (0, "test"),
    b: list[int | str] = [0, "test"],
    c: dict[str, Any] = {"0": True},
    d: set[float] = {0.0, 1.0, 2.0},
    **kwargs,
):
    """Do this and that."""

@decorator
class Classy(Parent):
    """A classy class."""

    def __init__(self, a: str, b: list[bool], *args, **kwargs):
        """Initialize the object."""

    @staticmethod
    def static_method(i: int):
        """Statically classy."""

    def method(self, j: str):
        pass
```

### `test_render.test_postrender_decorator`

```python
test_postrender_decorator():
```

Test the output of the `@postrender` decorator.

```python
def _func():
    pass
```

### `test_render.test_alternate_config`

```python
test_alternate_config():
```

Test for different configuration options.

```python
def func():
    pass

class Classy:
    def __init__(self, n):
        pass
```
