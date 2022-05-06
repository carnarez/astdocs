"""All tests related to the `astdocs.format_annotation()` function."""

import ast

from astdocs import format_annotation


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
    assert format_annotation(n.decorator_list[0]) == "decorator"

    # function
    n = ast.parse("@first\n@second\ndef func():\n    pass").body[0]
    assert [format_annotation(d) for d in n.decorator_list] == [
        "first",
        "second",
    ]


def test_complex_decorator():
    """Test for more complicated decoration (including arguments that are *not* parsed).

    ```python
    @decorator(including=parameter, and_with=another)
    def func():
        pass
    ```
    """
    n = ast.parse(
        "@decorator(including=parameter, and_with=another)\ndef func():\n    pass"
    ).body[0]

    assert [format_annotation(d) for d in n.decorator_list] == [
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
    s = "\n".join(
        [
            "import inlaws",
            "import foreign.family",
            "",
            "class Class(Parent, inlaws.Parent, foreign.family.Parent):",
            '    """Docstring"""',
        ]
    )
    n = ast.parse(s).body[2]

    assert [format_annotation(a) for a in n.bases] == [
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
    s = "\n".join(
        [
            "import typing",
            "",
            "def func(a, b: typing.Union[bool, str] = None, c: int = 0) -> str:",
            "    return str(j)",
        ]
    )
    n = ast.parse(s).body[1]

    assert [format_annotation(a.annotation) for a in n.args.args] == [
        "",
        "typing.Union[bool, str]",
        "int",
    ]

    assert format_annotation(n.returns) == "str"


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

    assert [format_annotation(a.annotation) for a in n.args.args] == [
        "",
        "bool | float | str",
        "int",
    ]

    assert format_annotation(n.returns) == "str"


def test_with_args_kwargs():
    """Test for presence of `*args` an `**kwargs` in function arguments (v3.10 syntax).

    ```python
    def func(a, *args, b: list[bool] = [True, False], **kwargs):
        pass
    ```
    """
    n = ast.parse(
        "def func(a, *args, b: list[bool] = [True, False], **kwargs):\n    pass"
    ).body[0]

    assert format_annotation(n.args.args[0].annotation) == ""
    assert format_annotation(n.args.kwonlyargs[0].annotation) == "list[bool]"


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
    s = "\n".join(
        [
            "import typing",
            "import package.module.submodule",
            "",
            "def func(",
            "    a: typing.Tuple[int, str],",
            "    b: typing.List[typing.Union[int, str]],",
            "    c: typing.Dict[str, typing.Any],",
            "    d: typing.Set[float],",
            "    e: package.module.submodule.Object,",
            "):",
            "    pass",
        ]
    )
    n = ast.parse(s).body[2]

    assert [format_annotation(a.annotation) for a in n.args.args] == [
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
        a: tuple[int, str],
        b: list[int | str],
        c: dict[str, Any],
        d: set[float],
        e: package.module.submodule.Object,
    ):
        pass
    ```
    """
    s = "\n".join(
        [
            "from typing import Any",
            "import package.module.submodule",
            "",
            "def func(",
            "    a: tuple[int, str],",
            "    b: list[int | str],",
            "    c: dict[str, Any],",
            "    d: set[float],",
            "    e: package.module.submodule.Object,",
            "):",
            "    pass",
        ]
    )
    n = ast.parse(s).body[2]

    assert [format_annotation(a.annotation) for a in n.args.args] == [
        "tuple[int, str]",
        "list[int | str]",
        "dict[str, Any]",
        "set[float]",
        "package.module.submodule.Object",
    ]
