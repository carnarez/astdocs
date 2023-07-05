"""Tests related to the environment (configuration) and the `cli()` function."""

import os
import subprocess

import pytest

import astdocs.astdocs


def test_runs() -> None:
    """Test successful run (this test checks nothing more than a script run).

    Equivalent to:

    ```shell
    $ python astdocs/astdocs.py astdocs/astdocs.py  # running on itself
    $ python astdocs/astdocs.py astdocs  # run on folder
    ```
    """
    subprocess.run(
        ["python", "astdocs/astdocs.py", "astdocs/astdocs.py"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["python", "astdocs/astdocs.py", "astdocs/"],
        capture_output=True,
    )


def test_faulty_run() -> None:
    """Test faulty run (no file nor code provided)."""
    with pytest.raises(SystemExit):
        astdocs.astdocs.cli()


def test_environment() -> None:
    """Test for environment variables.

    ```text
    ASTDOCS_BOUND_OBJECTS=on
    ASTDOCS_FOLD_ARGS_AFTER=100
    ASTDOCS_SHOW_PRIVATE=true
    ASTDOCS_SPLIT_BY=cfm
    ASTDOCS_WITH_LINENOS=1
    ```
    """
    os.environ["ASTDOCS_BOUND_OBJECTS"] = "on"
    os.environ["ASTDOCS_FOLD_ARGS_AFTER"] = "100"
    os.environ["ASTDOCS_SHOW_PRIVATE"] = "true"
    os.environ["ASTDOCS_SPLIT_BY"] = "cfm"
    os.environ["ASTDOCS_WITH_LINENOS"] = "1"

    assert astdocs.astdocs._update_configuration() == {
        "bound_objects": True,
        "fold_args_after": 100,
        "show_private": True,
        "split_by": "cfm",
        "with_linenos": True,
    }


def test_default_environment() -> None:
    """Test for environment variables (reset them for the tests).

    ```text
    ASTDOCS_BOUND_OBJECTS=off
    ASTDOCS_FOLD_ARGS_AFTER=88
    ASTDOCS_SHOW_PRIVATE=false
    ASTDOCS_SPLIT_BY=
    ASTDOCS_WITH_LINENOS=0
    ```
    """
    os.environ["ASTDOCS_BOUND_OBJECTS"] = "off"
    os.environ["ASTDOCS_FOLD_ARGS_AFTER"] = "88"
    os.environ["ASTDOCS_SHOW_PRIVATE"] = "false"
    os.environ["ASTDOCS_SPLIT_BY"] = ""
    os.environ["ASTDOCS_WITH_LINENOS"] = "0"

    assert astdocs.astdocs._update_configuration() == {
        "bound_objects": False,
        "fold_args_after": 88,
        "show_private": False,
        "split_by": "",
        "with_linenos": False,
    }


# S603: adding the noqa rule to avoid bandit false-positives; see the open issue at
#       https://github.com/PyCQA/bandit/issues/333
# S607: different path locally and within github runners; will keep a partial path and
#       ignore the associated warnings
# SLF001: we are calling hidden function *on purpose*
# ruff: noqa: S603,S607,SLF001
