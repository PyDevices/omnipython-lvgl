"""Sphinx configuration for the LVGL documentation.

Everything shared by the PyDevices documentation projects (theme, top bar,
Markdown and docstring setup, the reference map) comes from pydevices-docs.
The site covers omnipython-lvgl: the generator and the CPython, MicroPython
and CircuitPython ports built from it.
"""

from pydevices_docs import configure

globals().update(configure(
    "lvgl", __file__,
    repo="PyDevices/omnipython-lvgl", edit_path="docs",
    version_file=None,
))

# The data the API report reads stays in the repository, off the site.
exclude_patterns += [
    "README.md",
    "baseline",
]

# index.md is plain Markdown so the docs read on GitHub too; the site
# navigation lives in contents.md.
master_doc = "contents"
