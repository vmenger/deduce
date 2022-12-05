# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import toml
import datetime

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__name__)))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

toml_config = toml.load("../pyproject.toml")

project = toml_config['tool']['poetry']['name']
release = toml_config['tool']['poetry']['version']

author = toml_config['tool']['sphinx']['author']
copyright = f'{datetime.datetime.now().year}, {author}'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser'
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__getitem__,__setitem__,__len__,__eq__'
}

myst_heading_anchors = 3

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'karma_sphinx_theme'