"""Make `astdocs` installable (via `pip install git+https://...`)."""

import setuptools

setuptools.setup(
    author="carnarez",
    description=(
        "Opinionated way to pull and format NumPy-ish docstrings from Python modules."
    ),
    entry_points={"console_scripts": ["astdocs=astdocs.astdocs:cli"]},
    name="astdocs",
    packages=["astdocs"],
    package_data={"astdocs": ["py.typed"]},
    url="https://github.com/carnarez/astdocs",
    version="0.0.1",
)
