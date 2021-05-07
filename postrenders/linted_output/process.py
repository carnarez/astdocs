"""Pipe the output of `astdocs` to a linter.

As any other strictly-defined syntax, `Markdown` can (should?) be linted. This small
post-rendering does just that. (This will not be integrated to `astdocs` as it adds a
dependency, which is **out of scope**.)

The `Python` linter chosen for this example is
[`Mdformat`](https://github.com/executablebooks/mdformat), code style described
[there](https://mdformat.readthedocs.io/en/stable/users/style.html).
"""

import sys

import mdformat

import astdocs


def lint(md: str) -> str:
    """Lint the `Markdown`.

    Parameters
    ----------
    md : str
        The `Markdown` as outputted by `astdocs`.

    Returns
    -------
    : str
        Linted `Markdown`.
    """
    return mdformat.text(md)


@astdocs.postrender(lint)
def render(filepath: str) -> str:
    """Fetch/parse/render docstrings (simple wrapper function to allow decorators).

    Parameters
    ----------
    filepath : str
        Path to the `Python` module to be processed

    Returns
    -------
    : str
        The `Markdown` as outputted by `astdocs`.
    """
    return astdocs.render(filepath)


print(render(sys.argv[1]))
