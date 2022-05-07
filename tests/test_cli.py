"""Tests relate to the `cli()` function."""

import os
import subprocess

import pytest

import astdocs.astdocs


def test_runs():
    """Test faulty run."""
    assert subprocess.run(
        ["python", "astdocs/astdocs.py", "astdocs/astdocs.py"], capture_output=True
    )
    assert subprocess.run(
        ["python", "astdocs/astdocs.py", "astdocs"], capture_output=True
    )


def test_faulty_run():
    """Test faulty run."""
    with pytest.raises(SystemExit):
        astdocs.astdocs.cli()


def test_environment():
    """Test for environment variables."""
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


def test_default_environment():
    """Test for environment variables."""
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
