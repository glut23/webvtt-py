# Configuration file for the Sphinx documentation builder.

import sys
from pathlib import Path
from datetime import date

# Add parent dir to path
parent_directory = Path(__file__).parent.parent.parent.resolve()
sys.path.append(str(parent_directory))

import webvtt  # noqa

# -- Project information

project = 'webvtt-py'
copyright = f'2016-{date.today().year}, {webvtt.__author__}'
author = webvtt.__author__

release = webvtt.__version__
version = webvtt.__version__

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
# -- Options for manual page output
man_pages = [
    ('cli', 'webvtt', 'segment, shift and sync WebVTT captions', [author], 1),
]
