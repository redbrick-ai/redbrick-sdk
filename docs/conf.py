"""Configuration file for the Sphinx documentation builder."""

# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../"))
# pylint: disable=wrong-import-position
from redbrick import __version__ as sdk_version  # noqa: E402

# pylint: disable=invalid-name

# -- Project information -----------------------------------------------------

project = "RedBrick AI"
copyright = "2023, RedBrick AI"  # pylint: disable=redefined-builtin
author = "RedBrick AI"

version = sdk_version
release = version


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "recommonmark",
    "sphinxarg.ext",
    "sphinx_inline_tabs",
    "sphinxcontrib.autoprogram",
    "sphinx_autodoc_typehints",
    "sphinx_design",
    "sphinx_copybutton",
]
# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # type: ignore

# Set some RTD theme config.  This includes the entire navigation structure
# into the sidebar of all pages.  However, expanding the sections isn't
# provided yet on the RTD theme (see
# https://github.com/readthedocs/sphinx_rtd_theme/issues/455).
html_static_path = ["_static"]
autodoc_member_order = "bysource"
autodoc_inherit_docstrings = False
html_title = f"Version {version}"
html_favicon = "_static/favicon.ico"

# https://pradyunsg.me/furo/customisation
html_theme_options = {
    "light_logo": "redbrick.svg",
    "dark_logo": "redbrick--darkmode.svg",
    "source_repository": "https://github.com/redbrick-ai/redbrick-sdk/",
    "source_branch": "master",
    "source_directory": "docs/",
    "navigation_with_keys": True,
    "top_of_page_button": None,
}
