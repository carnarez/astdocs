"""All tests related to the `astdocs.parse_*()` functions.

Expected/supported objects are:
* `ClassDef` (`parse_classdef()`),
* `FunctionDef` or `AsyncFunctionDef` (`parse_functiondef()`),
* `Import` or `ImportFrom` (`parse_import()`).
"""

import ast

from astdocs import parse_classdef, parse_functiondef, parse_import, parse_tree
