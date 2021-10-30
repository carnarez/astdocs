"""Make `astdocs` installable (via `pip install git+https://...`)."""

import setuptools  # type: ignore

setuptools.setup(
    author="carnarez",
    description=(
        "Opinionated way to pull and format NumPy-ish docstrings from Python modules."
    ),
    entry_points={"console_scripts": ["astdocs=astdocs.astdocs:main"]},
    name="astdocs",
    package_data={"astdocs": ["*.pyi", "py.typed"]},
    packages=["astdocs"],
    url="https://github.com/carnarez/astdocs",
    version="0.0.1",
)
