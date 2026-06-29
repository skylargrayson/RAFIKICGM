# Configuration file for the Sphinx documentation builder.
#
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
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../rafiki'))


# -- Project information -----------------------------------------------------

project = 'RAFIKI-CGM'
copyright = '2026, Skylar Grayson'
author = 'Skylar Grayson'

# The full version, including alpha/beta/rc tags
release = '0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc','sphinxcontrib.mermaid']


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

html_theme_options = {
      "globaltoc_includehidden": True,
    # --- Colors ---
    'body_text': '#333333',
    'header_text': '#ffffff',          # text in the header bar
    'navbar_link': '#ffffff', 
    'sidebar_header': '#3E4D6C',       # sidebar section headers
    'sidebar_text': '#333333',
    'sidebar_link': '#3E4D6C',
    'anchor': '#3E4D6C',               # hyperlink color
    'anchor_hover_fg': '#7C4DFF',      # hyperlink hover color
    'note_bg': '#e8f0fe',              # background of note boxes
    'note_border': '#3E4D6C',
    'warn_bg': '#fff3e0',
    'warn_border': '#ff9800',
    'pre_bg': '#f8f8f8',               # code lock background

    # --- Header bar background ---
    'gray_1': '#3E4D6C',               # header/footer background

    # --- Width ---
    'page_width': '1100px',            # default is 940px 
    'sidebar_width': '270px',          # default is 220px

    # --- Logo and description ---
    'logo': 'images/logo.png',
    'logo_name': True,
    'description': 'Mock data of the hot CGM in cosmological simulations',
    'github_user': 'yourusername',
    'github_repo': 'rafiki-cgm',
    'github_button': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']