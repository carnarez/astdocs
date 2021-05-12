"""Make `astdocs` installable (including `pip install git+https://...`)."""

import setuptools

with open("README.md") as f:
    desc = f.read()

setuptools.setup(
    name="astdocs",
    version="0.0.1",
    author="carnarez",
    description=desc,
    url="https://github.com/carnarez/astdocs",
    packages=setuptools.find_packages(where="astdocs"),
)
