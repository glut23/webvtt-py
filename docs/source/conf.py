# Configuration file for the Sphinx documentation builder.

import sys
import tomllib
from pathlib import Path
from datetime import date

# Add parent dir to the start of the path, so the repo is documented instead
# of any installed webvtt
parent_directory = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(parent_directory))

import webvtt  # noqa

# -- Project information

with open(parent_directory / 'pyproject.toml', 'rb') as pyproject:
    author = tomllib.load(pyproject)['project']['authors'][0]['name']

project = 'webvtt-py'
copyright = f'2016-{date.today().year}, {author}'

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
    ('cli', 'webvtt', 'segment, shift, sync and validate WebVTT captions',
     [author], 1),
]
