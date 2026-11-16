# ruff: noqa: SLF001

"""Tests related to the environment (configuration) and the `cli()` function."""

import pathlib
import subprocess
import sys

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
        [sys.executable, "astdocs/astdocs.py", "astdocs/astdocs.py"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [sys.executable, "astdocs/astdocs.py", "astdocs/"],
        capture_output=True,
        check=True,
    )


def test_cli_file(capsys: pytest.CaptureFixture) -> None:
    """Test the `cli()` function on a single module.

    ```shell
    $ astdocs astdocs/astdocs.py
    ```
    """
    astdocs.astdocs.cli(["astdocs/astdocs.py"])

    assert capsys.readouterr().out.startswith("# Module `astdocs.astdocs`")


def test_cli_folder(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture) -> None:
    '''Test the `cli()` function on a folder, including hidden and invalid modules.

    ```text
    tmp_path/
    ├── .venv/
    │   └── leaked.py
    ├── broken.py  # invalid syntax
    └── visible.py
    ```

    ```python
    def func():
        """Visible."""
    ```
    '''
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "leaked.py").write_text('def func():\n    """Hidden."""')
    (tmp_path / "broken.py").write_text("def func(:\n    pass")
    (tmp_path / "visible.py").write_text('def func():\n    """Visible."""')

    astdocs.astdocs.cli([str(tmp_path)])
    captured = capsys.readouterr()

    assert "visible.func" in captured.out
    assert "leaked" not in captured.out
    assert "broken" not in captured.out
    assert f"Skipping {tmp_path / 'broken.py'}" in captured.err


def test_faulty_run() -> None:
    """Test faulty runs (no path, too many paths, or path not found)."""
    with pytest.raises(SystemExit):
        astdocs.astdocs.cli([])

    with pytest.raises(SystemExit):
        astdocs.astdocs.cli(["astdocs/astdocs.py", "astdocs/__init__.py"])

    with pytest.raises(SystemExit):
        astdocs.astdocs.cli(["does/not/exist.py"])


def test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test for environment variables.

    ```text
    ASTDOCS_BOUND_OBJECTS=on
    ASTDOCS_FOLD_ARGS_AFTER=100
    ASTDOCS_SHOW_PRIVATE=true
    ASTDOCS_SPLIT_BY=cfm
    ASTDOCS_WITH_LINENOS=1
    ```
    """
    monkeypatch.setattr(astdocs.astdocs, "config", astdocs.astdocs.config.copy())
    monkeypatch.setenv("ASTDOCS_BOUND_OBJECTS", "on")
    monkeypatch.setenv("ASTDOCS_FOLD_ARGS_AFTER", "100")
    monkeypatch.setenv("ASTDOCS_SHOW_PRIVATE", "true")
    monkeypatch.setenv("ASTDOCS_SPLIT_BY", "cfm")
    monkeypatch.setenv("ASTDOCS_WITH_LINENOS", "1")

    assert astdocs.astdocs._update_configuration() == {
        "bound_objects": True,
        "fold_args_after": 100,
        "show_private": True,
        "split_by": "cfm",
        "with_linenos": True,
    }


def test_default_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test for environment variables (none set: defaults).

    ```text
    ASTDOCS_BOUND_OBJECTS=
    ASTDOCS_FOLD_ARGS_AFTER=
    ASTDOCS_SHOW_PRIVATE=
    ASTDOCS_SPLIT_BY=
    ASTDOCS_WITH_LINENOS=
    ```
    """
    monkeypatch.setattr(astdocs.astdocs, "config", astdocs.astdocs.config.copy())
    for v in (
        "BOUND_OBJECTS",
        "FOLD_ARGS_AFTER",
        "SHOW_PRIVATE",
        "SPLIT_BY",
        "WITH_LINENOS",
    ):
        monkeypatch.delenv(f"ASTDOCS_{v}", raising=False)

    assert astdocs.astdocs._update_configuration() == {
        "bound_objects": False,
        "fold_args_after": 88,
        "show_private": False,
        "split_by": "",
        "with_linenos": False,
    }
