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
    assert [format_annotation(d, "@") for d in n.decorator_list] == ["@decorator"]

    # function
    n = ast.parse("@first\n@second\ndef func():\n    pass").body[0]
    assert [format_annotation(d, "@") for d in n.decorator_list] == [
        "@first",
        "@second",
    ]


def test_complex_decorator():
    """Test for more complicated decoration (including arguments that are *not* parsed).

    ```python
    @decorator(including=parameter)
    def func():
        pass
    ```
    """
    n = ast.parse("@decorator(including=parameter)\ndef func():\n    pass").body[0]
    assert [format_annotation(d, "@") for d in n.decorator_list] == ["@decorator()"]


def test_function_simple_input_output():
    """Test for simple input/output arguments.

    ```python
    def func(i, j: int, k: int = 0) -> str:
        pass
    ```
    """
    n = ast.parse(
        "def func(a, b: bool | str, c: int = 0) -> str:\n    return str(j)"
    ).body[0]

    assert [format_annotation(a.annotation) for a in n.args.args] == [
        "",
        "bool | str",
        "int",
    ]

    assert format_annotation(n.returns) == "str"


def test_function_complex_input_output():
    """Test for simple input/output arguments.

    ```python
    from typing import Any

    def func(
        a: tuple[int, str], b: list[int], c: dict[str, Any], d: set[float]
    ):
        pass
    ```

    Notes
    -----
    Keeping this test if one day parsing the content within `dict`/`list`/`set`/`tuple`
    objects gets supported.
    """
    s = "\n".join(
        [
            "from typing import Any",
            "",
            "def func(",
            "    a: tuple[int, str], b: list[int], c: dict[str, Any], d: set[float]",
            "):",
            "    pass",
        ]
    )
    n = ast.parse(s).body[1]

    assert [format_annotation(a.annotation) for a in n.args.args] == [
        "tuple",
        "list",
        "dict",
        "set",
    ]
