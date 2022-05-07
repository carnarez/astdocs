"""All tests related to the `astdocs.render_*()` functions."""

import ast

import astdocs
import astdocs.astdocs

MODULE: str = "test"


def test_empty():
    """Test for no input (just to get 100% coverage)."""
    assert astdocs.render() == "Nothing to do."


def test_remove_from_path():
    """Test with the `remove_from_path` argument (just to get 100% coverage)."""
    assert astdocs.render(filepath=f"./tests/{__name__}.py", remove_from_path="./")


def test_simple_class():
    '''Test for simple class rendering.

    ```python
    class Classy:
        """A classy class."""

        def method(self, i: str):
            """Methodically classy."""
    ```
    '''
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}
    astdocs.astdocs._update_templates(astdocs.config)

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

* [`static_method()`](#testclassystatic_method)
* [`method()`](#testclassymethod): Methodically classy.

#### Constructor

```python
Classy(a: str, b: list[bool], **kwargs)
```



#### Methods

##### `test.Classy.static_method`

```python
static_method(i: int):
```



**Decoration** via `@staticmethod`.

##### `test.Classy.method`

```python
method(j: str) -> str:
```

Methodically classy.
    """.strip()

    n = ast.parse(s)
    classes, functions, imports = astdocs.parse(n, MODULE, MODULE)
    rendered = astdocs.render_class(
        f"{MODULE}.py", f"{MODULE}.Classy", classes, functions
    )

    assert rendered == r


def test_complex_class():
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
    astdocs.astdocs._update_templates(astdocs.config)

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
        f"{MODULE}.py", f"{MODULE}.Classy", classes, functions
    )

    assert rendered == r


def test_complex_function():
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
    astdocs.astdocs._update_templates(astdocs.config)

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


def test_private_hidden_objects():
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


def test_private_visible_objects():
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


def test_it_all():
    '''Test for class including `__init__` and methods.

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
    astdocs.astdocs._update_templates(astdocs.config)

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
