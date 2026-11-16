# mypy: disable-error-code="arg-type,attr-defined"
# ruff: noqa: RUF059

"""All tests related to the `astdocs.render_*()` functions."""

import ast
import pathlib

import astdocs
import astdocs.astdocs

MODULE: str = "test"


def test_empty() -> None:
    """Test for no input (just to get 100% coverage)."""
    assert astdocs.render() == "Nothing to do."


def test_remove_from_path() -> None:
    """Test with the `remove_from_path` argument (just to get 100% coverage).

    This test checks literally *nothing* more than the `remove_from_path` flag of the
    `render()` function. Return is ignored.
    """
    astdocs.render(filepath="./tests/test_render.py", remove_from_path="./")


def test_simple_class() -> None:
    '''Test for simple class rendering.

    ```python
    class Classy:
        """A classy class."""

        def method(self, i: str):
            """Methodically classy."""
    ```
    '''
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}

    # source
    s = '''
class Classy:
    """A classy class."""

    def method(self, j: str) -> str:
        """Methodically classy."""
    '''.strip()

    # target
    r = """
### `test.Classy`

A classy class.



**Methods**

* [`method()`](#testclassymethod): Methodically classy.

#### Constructor

```python
Classy()
```



#### Methods

##### `test.Classy.method`

```python
method(j: str) -> str:
```

Methodically classy.
    """.strip()

    n = ast.parse(s)
    classes, functions, imports = astdocs.parse(n, MODULE, MODULE)
    rendered = astdocs.render_class(
        f"{MODULE}.py",
        f"{MODULE}.Classy",
        classes,
        functions,
    )

    assert rendered == r


def test_complex_class() -> None:
    '''Test for class including `__init__` and methods.

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
    '''
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}

    # source
    s = '''
@decorator
class Classy(Parent):
    """A classy class."""

    def __init__(self, a: str, b: list[bool], *args, **kwargs):
        """Initialize the classy object."""

    @staticmethod
    def static_method(i: int):
        """Statically classy."""

    def method(self, j: str) -> str:
        pass
    '''.strip()

    # target
    r = """
### `test.Classy`

A classy class.

**Decoration** via `@decorator`.

**Methods**

* [`static_method()`](#testclassystatic_method): Statically classy.
* [`method()`](#testclassymethod)

#### Constructor

```python
Classy(a: str, b: list[bool], *args, **kwargs)
```

Initialize the classy object.

#### Methods

##### `test.Classy.static_method`

```python
static_method(i: int):
```

Statically classy.

**Decoration** via `@staticmethod`.

##### `test.Classy.method`

```python
method(j: str) -> str:
```
    """.strip()

    n = ast.parse(s)
    classes, functions, imports = astdocs.parse(n, MODULE, MODULE)
    rendered = astdocs.render_class(
        f"{MODULE}.py",
        f"{MODULE}.Classy",
        classes,
        functions,
    )

    assert rendered == r


def test_complex_function() -> None:
    '''Test for complex input/output arguments.

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
    '''
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}

    # source
    s = '''
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
    '''.strip()

    # target
    r = """
### `test.func`

```python
func(
    *args,
    a: tuple[int, str] = (0, "test"),
    b: list[int | str] = [0, "test"],
    c: dict[str, Any] = {"0": True},
    d: set[float] = {0.0, 1.0, 2.0},
    **kwargs,
):
```

Do this and that.

**Decoration** via `@decorator`.
    """.strip()

    n = ast.parse(s).body[1]
    functions = astdocs.parse_function(n, MODULE, MODULE, {})
    rendered = astdocs.render_function(f"{MODULE}.py", f"{MODULE}.func", functions)

    assert rendered == r


def test_many_parameters() -> None:
    '''Test rendering for function/method with many parameters.

    ```python
    def function(param1: float,
                 param2: int,
                 param3: str,
                 param4: str,
                 param5: list[str] = [],
                 param6: tuple[float, float, float] = (),
                 param7: dict[int, str] = [],
                 *args,
                 **kwargs):
        """This does everything and more."""

    class Classy(Parent):
        """A classy class."""

        def method(
            self,
            param1: float,
            param2: int,
            param3: str,
            param4: str,
            param5: list[str] = [],
            param6: tuple[float, float, float] = (),
            param7: dict[int, str] = [],
            *args,
            **kwargs,
        ):
            pass
    ```
    '''
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}

    # source
    s = '''
def function(param1: float,
             param2: int,
             param3: str,
             param4: str,
             param5: list[str] = [],
             param6: tuple[float, float, float] = (),
             param7: dict[int, str] = [],
             *args,
             **kwargs):
    """This does everything and more."""

class Classy(Parent):
    """A classy class."""

    def method(
        self,
        param1: float,
        param2: int,
        param3: str,
        param4: str,
        param5: list[str] = [],
        param6: tuple[float, float, float] = (),
        param7: dict[int, str] = [],
        *args,
        **kwargs,
    ):
        pass
    '''.strip()

    # target
    r = """
# Module `test`

**Functions**

* [`function()`](#testfunction): This does everything and more.

**Classes**

* [`Classy`](#testclassy): A classy class.

## Functions

### `test.function`

```python
function(
    param1: float,
    param2: int,
    param3: str,
    param4: str,
    param5: list[str] = [],
    param6: tuple[float, float, float] = (),
    param7: dict[int, str] = [],
    *args,
    **kwargs,
):
```

This does everything and more.

## Classes

### `test.Classy`

A classy class.

**Methods**

* [`method()`](#testclassymethod)

#### Constructor

```python
Classy()
```

#### Methods

##### `test.Classy.method`

```python
method(
    param1: float,
    param2: int,
    param3: str,
    param4: str,
    param5: list[str] = [],
    param6: tuple[float, float, float] = (),
    param7: dict[int, str] = [],
    *args,
    **kwargs,
):
```
    """.strip()

    n = ast.parse(s)
    classes, functions, imports = astdocs.parse(n, MODULE, MODULE)
    rendered = astdocs.render(code=s, module=MODULE)

    assert rendered == r


def test_private_hidden_objects() -> None:
    '''Test for private objects.

    ```python
    def _hidden():
        """Am hiding."""

    class _Hidden:
        """Am hiding."""
    ```
    '''
    config = astdocs.config.copy()
    config.update({"show_private": False})

    # source
    s = 'def _hidden():\n    """Am hiding."""\n\nclass _Hidden:\n    """Am hiding."""'

    # target
    r = "# Module `test`"

    rendered = astdocs.render(code=s, module=MODULE, config=config)

    assert rendered == r


def test_private_visible_objects() -> None:
    '''Test for visible private objects.

    ```python
    def _hidden():
        """Am hiding."""

    class _Hidden:
        """Am hiding."""
    ```
    '''
    config = astdocs.config.copy()
    config.update({"show_private": True})

    # source
    s = 'def _hidden():\n    """Am hiding."""\n\nclass _Hidden:\n    """Am hiding."""'

    # target
    r = """
# Module `test`

**Functions**

* [`_hidden()`](#test_hidden): Am hiding.

**Classes**

* [`_Hidden`](#test_hidden): Am hiding.

## Functions

### `test._hidden`

```python
_hidden():
```

Am hiding.

## Classes

### `test._Hidden`

Am hiding.

#### Constructor

```python
_Hidden()
```
    """.strip()

    rendered = astdocs.render(code=s, module=MODULE, config=config)

    assert rendered == r


def test_it_all() -> None:
    '''Test for a full example (concatention of other snippets).

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
    '''
    # source
    s = '''
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
        """Initialize the classy object."""

    @staticmethod
    def static_method(i: int):
        """Statically classy."""

    def method(self, j: str) -> str:
        pass
    '''.strip()

    # target
    r = """
# Module `test`

**Functions**

* [`func()`](#testfunc): Do this and that.

**Classes**

* [`Classy`](#testclassy): A classy class.

## Functions

### `test.func`

```python
func(
    *args,
    a: tuple[int, str] = (0, "test"),
    b: list[int | str] = [0, "test"],
    c: dict[str, Any] = {"0": True},
    d: set[float] = {0.0, 1.0, 2.0},
    **kwargs,
):
```

Do this and that.

**Decoration** via `@decorator`.

## Classes

### `test.Classy`

A classy class.

**Decoration** via `@decorator`.

**Methods**

* [`static_method()`](#testclassystatic_method): Statically classy.
* [`method()`](#testclassymethod)

#### Constructor

```python
Classy(a: str, b: list[bool], *args, **kwargs)
```

Initialize the classy object.

#### Methods

##### `test.Classy.static_method`

```python
static_method(i: int):
```

Statically classy.

**Decoration** via `@staticmethod`.

##### `test.Classy.method`

```python
method(j: str) -> str:
```
    """.strip()

    rendered = astdocs.render(code=s, module=MODULE)

    assert rendered == r


def _add_header(md: str) -> str:
    """Add an extra header to the `Markdown` output.

    Parameters
    ----------
    md : str
        `Markdown` to process.

    Returns
    -------
    : str
        Processed `Markdown`.

    """
    return f"Header\n\n{md}"


@astdocs.postrender(_add_header)
def _render(code: str, module: str) -> str:
    """Wrap `astdocs` rendering function.

    Parameters
    ----------
    code : str
        Code to process; useful when used as a module.
    module : str
        Name of the current module. Defaults to empty string.

    Returns
    -------
    : str
        Processed input.

    """
    return astdocs.render(code=code, module=module)


def test_postrender_decorator() -> None:
    """Test the output of the `@postrender` decorator.

    ```python
    def _func():
        pass
    ```
    """
    assert _render("def _func():\n    pass", MODULE) == "Header\n\n# Module `test`"


def test_alternate_config() -> None:
    """Test for different configuration options.

    ```python
    def func():
        pass

    class Classy:
        def __init__(self, n):
            pass
    ```

    with

    ```python
    config.update({"bound_objects": True, "split_by": "cfm", "with_linenos": True})
    ```
    """
    config = astdocs.config.copy()
    config.update({"bound_objects": True, "split_by": "cfm", "with_linenos": True})

    # source
    s = """
def func(a):
    pass

class Classy:

    def __init__(self):
        pass

    def method(self, b):
        pass
    """.strip()

    # target
    r = """
%%%BEGIN MODULE test
%%%START MODULE test
# Module `test`

%%%END MODULE test

%%%BEGIN FUNCTIONDEF test.func
%%%START FUNCTIONDEF test.func
# `test.func`

```python
func(a):
```

%%%SOURCE test.py:1:2
%%%END FUNCTIONDEF test.func

%%%BEGIN CLASSDEF test.Classy
%%%START CLASSDEF test.Classy
# `test.Classy`

**Methods**

* [`method()`](#testclassymethod)

%%%SOURCE test.py:4:10

## Constructor

```python
Classy()
```

%%%SOURCE test.py:6:7

## Methods

%%%BEGIN FUNCTIONDEF test.Classy.method
%%%START FUNCTIONDEF test.Classy.method
### `test.Classy.method`

```python
method(b):
```

%%%SOURCE test.py:9:10
%%%END FUNCTIONDEF test.Classy.method
%%%END CLASSDEF test.Classy
    """.strip()

    rendered = astdocs.render(code=s, module=MODULE, config=config)

    assert rendered == r


def test_successive_configurations() -> None:
    """Test successive renderings with different configurations do not interfere.

    ```python
    class Classy:
        pass
    ```
    """
    s = "class Classy:\n    pass"
    bound = astdocs.config.copy()
    bound.update({"bound_objects": True, "split_by": "c"})

    first = astdocs.render(code=s, module=MODULE, config=bound)
    astdocs.render(code=s, module=MODULE)
    astdocs.render(code=s, module=MODULE, config=bound)

    assert astdocs.render(code=s, module=MODULE, config=bound) == first
    assert first.count("%%%BEGIN CLASSDEF") == 1
    assert first.count("%%%START CLASSDEF") == 1
    assert "%%%" not in astdocs.render(code=s, module=MODULE)


def test_remove_from_path_elsewhere(tmp_path: pathlib.Path) -> None:
    '''Test the `remove_from_path` argument with a file outside the working directory.

    ```python
    def func():
        """Somewhere else."""
    ```
    '''
    (tmp_path / "package").mkdir()
    (tmp_path / "package" / "__init__.py").write_text('"""Package."""')
    (tmp_path / "package" / "module.py").write_text('def func():\n    """Else."""')

    for f, m in (("module.py", "package.module"), ("__init__.py", "package")):
        rendered = astdocs.render(
            filepath=str(tmp_path / "package" / f),
            remove_from_path=f"{tmp_path}/",
        )

        assert rendered.startswith(f"# Module `{m}`")


def test_nested_objects() -> None:
    '''Test for classes and functions defined within classes and methods.

    ```python
    class Outer:
        """Outer."""

        class Inner:
            """Inner."""

            def inner_method(self):
                """Inner method."""

        def method(self):
            """Method."""

            def nested():
                pass
    ```
    '''
    s = '''
class Outer:
    """Outer."""

    class Inner:
        """Inner."""

        def inner_method(self):
            """Inner method."""

    def method(self):
        """Method."""

        def nested():
            pass
    '''.strip()

    r = """
# Module `test`

**Classes**

* [`Outer`](#testouter): Outer.

## Classes

### `test.Outer`

Outer.

**Methods**

* [`method()`](#testoutermethod): Method.

#### Constructor

```python
Outer()
```

#### Methods

##### `test.Outer.method`

```python
method():
```

Method.

### `test.Outer.Inner`

Inner.

**Methods**

* [`inner_method()`](#testouterinnerinner_method): Inner method.

#### Constructor

```python
Inner()
```

#### Methods

##### `test.Outer.Inner.inner_method`

```python
inner_method():
```

Inner method.
    """.strip()

    assert astdocs.render(code=s, module=MODULE) == r
