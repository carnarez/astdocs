"""All tests related to the `astdocs.parse_*()` function."""

import ast

import astdocs

MODULE: str = "test"


def test_simple_decorator():
    '''Test for decoration parsing.

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
    '''
    # class
    n = ast.parse('@decorator\nclass Classy:\n    """Docstring"""').body[0]

    assert astdocs.parse_annotation(n.decorator_list[0]) == "decorator"

    # function
    n = ast.parse("@first\n@second\ndef func():\n    pass").body[0]

    assert [astdocs.parse_annotation(d) for d in n.decorator_list] == [
        "first",
        "second",
    ]


def test_complex_decorator():
    """Test for more complicated decoration.

    ```python
    @decorator(including=parameter, and_with=another)
    def func():
        pass
    ```
    """
    n = ast.parse(
        "@decorator(including=parameter, and_with=another)\ndef func():\n    pass"
    ).body[0]

    assert [astdocs.parse_annotation(d) for d in n.decorator_list] == [
        "decorator(including=parameter, and_with=another)"
    ]


def test_inheritance():
    '''Test for multiple inheritance.

    ```python
    import inlaws
    import foreign.family

    class Class(Parent, inlaws.Parent, foreign.family.Parent):
        """Docstring"""
    ```
    '''
    # source
    s = '''
import inlaws
import foreign.family

class Class(Parent, inlaws.Parent, foreign.family.Parent):
    """Docstring"""
    '''.strip()
    n = ast.parse(s).body[2]

    assert [astdocs.parse_annotation(a) for a in n.bases] == [
        "Parent",
        "inlaws.Parent",
        "foreign.family.Parent",
    ]


def test_simple_parameters_typing():
    """Test for simple input/output arguments.

    ```python
    import typing

    def func(a, b: typing.Union[bool, str] = None, c: int = 0) -> str:
        return str(j)
    ```
    """
    # source
    s = """
import typing

def func(a, b: typing.Union[bool, str] = None, c: int = 0) -> str:
    return str(j)
    """.strip()
    n = ast.parse(s).body[1]

    assert [astdocs.parse_annotation(a.annotation) for a in n.args.args] == [
        "",
        "typing.Union[bool, str]",
        "int",
    ]

    assert astdocs.parse_annotation(n.returns) == "str"


def test_simple_parameters_v310():
    """Test for simple input/output arguments (v3.10 syntax).

    ```python
    def func(a, b: bool | float | str, c: int = 0) -> str:
        return str(j)
    ```
    """
    n = ast.parse(
        "def func(a, b: bool | float | str, c: int = 0) -> str:\n    return str(j)"
    ).body[0]

    assert [astdocs.parse_annotation(a.annotation) for a in n.args.args] == [
        "",
        "bool | float | str",
        "int",
    ]

    assert astdocs.parse_annotation(n.returns) == "str"


def test_with_args_kwargs():
    """Test for presence of `*args` and `**kwargs` in function arguments (v3.10 syntax).

    ```python
    def func(a, *args, b: list[bool] = [True, False], **kwargs):
        pass
    ```
    """
    n = ast.parse(
        "def func(a, *args, b: list[bool] = [True, False], **kwargs):\n    pass"
    ).body[0]

    assert astdocs.parse_annotation(n.args.args[0].annotation) == ""
    assert astdocs.parse_annotation(n.args.kwonlyargs[0].annotation) == "list[bool]"


def test_complex_parameters_typing():
    """Test for complex input/output arguments.

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
    """
    # source
    s = """
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
    """.strip()
    n = ast.parse(s).body[2]

    assert [astdocs.parse_annotation(a.annotation) for a in n.args.args] == [
        "typing.Tuple[int, str]",
        "typing.List[typing.Union[int, str]]",
        "typing.Dict[str, typing.Any]",
        "typing.Set[float]",
        "package.module.submodule.Object",
    ]


def test_complex_parameters_v310():
    """Test for complex input/output arguments (v3.10 syntax).

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
    """
    # source
    s = """
from typing import Any
import package.module.submodule

def func(
    a: tuple[int, str] = (0, "test"),
    b: list[int | str] = [0, "test"],
    c: dict[str, Any] = {"0": True},
    d: set[float] = {0.0, 1.0, 2.0},
):
    pass
    """.strip()
    n = ast.parse(s).body[2]

    assert [astdocs.parse_annotation(a.annotation) for a in n.args.args] == [
        "tuple[int, str]",
        "list[int | str]",
        "dict[str, Any]",
        "set[float]",
    ]


def test_class():
    """Test for class including `__init__` and methods.

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
    """
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}

    # source
    s = """
class Classy:

    def __init__(self, a: str, b: list[bool], **kwargs):
        pass

    @staticmethod
    def static_method(i: int):
        pass

    def method(self, j: str):
        pass
    """.strip()
    n = ast.parse(s)
    classes, functions, imports = astdocs.parse(n, MODULE, MODULE)

    assert astdocs.objects[MODULE]["classes"] == {"Classy": f"{MODULE}.Classy"}
    assert astdocs.objects[MODULE]["functions"] == {
        "Classy.__init__": f"{MODULE}.Classy.__init__",
        "Classy.method": f"{MODULE}.Classy.method",
        "Classy.static_method": f"{MODULE}.Classy.static_method",
    }


def test_function():
    """Test for a simple function.

    ```python
    def func(a, b: bool | float | str = "", c: int = 0) -> str:
        return str(j)
    ```
    """
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}

    n = ast.parse(
        "def func(a, b: bool | float | str, c: int = 0) -> str:\n    return str(j)"
    )
    astdocs.parse(n, MODULE, MODULE)

    assert astdocs.objects[MODULE]["functions"] == {"func": f"{MODULE}.func"}


def test_import():
    """Test for a simple function.

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
    """
    astdocs.objects[MODULE] = {"classes": {}, "functions": {}, "imports": {}}

    # source
    s = """
import module
import module1, module2, module3
import package.module
import package.module.submodule as alias
from .. import *
from .module import Object, function
from module.submodule import AnotherObject as ThatObject
from package.module.submodule import YetAnotherObject as short_alias
    """.strip()
    n = ast.parse(s)
    astdocs.parse(n, MODULE, MODULE)

    assert astdocs.objects[MODULE]["imports"] == {
        "*": "test....*",
        "Object": "test...module.Object",
        "ThatObject": "test.module.submodule.AnotherObject",
        "alias": "test.package.module.submodule",
        "function": "test...module.function",
        "module": "test.module",
        "module1": "test.module1",
        "module2": "test.module2",
        "module3": "test.module3",
        "package.module": "test.package.module",
        "short_alias": "test.package.module.submodule.YetAnotherObject",
    }
