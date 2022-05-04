"""All tests related to the `astdocs.render_*()` functions.

Applies to the following objects:
* class (`render_classdef()`),
* function (`render_functiondef()`),
* module (`render_module()`).
"""

import ast

from astdocs import render_classdef, render_functiondef, render_module
