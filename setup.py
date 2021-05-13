"""Make `astdocs` installable (via `pip install git+https://...`)."""

import setuptools

setuptools.setup(
    name="astdocs",
    version="0.0.1",
    author="carnarez",
    description=(
        "Opinionated way to pull and format NumPy-ish docstrings from Python modules."
    ),
    url="https://github.com/carnarez/astdocs",
    packages=["astdocs"],
    entry_points={"console_scripts": ["astdocs=astdocs.astdocs:__cli__"]},
)
