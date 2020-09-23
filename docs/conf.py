# Configuration file for the Sphinx documentation builder.
#
# Requires: sphinx, sphinx_rtd_theme, sphinx-autodocgen
# With run: python -m sphinx -M html docs docs/_build -W
#

import os
import sys
from sphinx.util import logging
logger = logging.getLogger('conf.py')

DOCS_DIR = os.path.dirname(__file__)

sys.path.append(DOCS_DIR+'/..')

# -- Project information -----------------------------------------------------

from datetime import date
author = 'Ben Spiller'
copyright = f'{date.today().year} {author}; documentation last updated on {date.today().strftime("%Y-%m-%d")}'

# The full version, including alpha/beta/rc tags
with open(DOCS_DIR+'/../VERSION', encoding='ascii') as versionfile:
	this_release = versionfile.read().strip()

project = f'PySys Java plugins v{this_release}'

# -- General configuration ---------------------------------------------------

import sphinxcontrib_autodocgen

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.viewcode',
	'sphinx.ext.intersphinx',
	'sphinxcontrib_autodocgen',
]

import pysysjava
autodocgen_config = {
	'modules':[pysysjava], 
	'generated_source_dir': DOCS_DIR+'/_autodocgen/',
	'skip_module_regex': '(.*[.]__)', # if module matches this then it and any of its submodules will be skipped
	'write_documented_items_output_file': DOCS_DIR+'/_build/autodocgen_documented_items.txt',
	'autodoc_options_decider': { },
	'module_title_decider': lambda modulename: 'API Reference' if modulename=='pysysjava' else modulename,
}

# Allow links to main PySys classes
intersphinx_mapping = {'pysys': ('https://pysys-test.github.io/pysys-test', None)}

default_role = 'py:obj' # So that `xxx` is converted to a Python reference. Use ``xxx`` for monospaced non-links.

# This enables linking to other documents
# To refer to another .rst document use                  :doc:`TestDescriptors`
# To refer to a section inside another .rst document use :ref:`TestDescriptors:Sample pysysdirconfig.xml`
autosectionlabel_prefix_document = True

autoclass_content = 'both' # include __init__ params in doc strings for class

autodoc_inherit_docstrings = False
autodoc_member_order = 'bysource' # bysource is usually a more logical order than alphabetical
autodoc_default_options = {
	'show-inheritance':True, # show the base class name
}

nitpicky = True # so we get warnings about broken links

def autodoc_skip_member(app, what, name, obj, skip, options):
	# nb: 'what' means the parent that the "name" item is in e.g. 'class', 'module'

	if skip: 
		# We don't want to hide protected class methods with a single underscore; but we do want to hide any 
		# that include a double-underscore since _classname__membername is how Python mangles private members
		if (name.startswith('_') and ('__' not in name) and what=='class' and callable(obj) 
				and obj.__doc__ and ':meta private:' not in obj.__doc__):
			logger.info(f'conf.py: UNSKIPPING protected class method: {name}')
			return False
		logger.debug(f'conf.py: ALREADY Skipping member: {name}')
		return None
		
	return None

autosummary_generate = True
autosummary_generate_overwrite = False


def setup(app):
	app.connect("autodoc-skip-member", autodoc_skip_member)

	def supportGitHubPages(app, exception):
		outputdir = os.path.abspath(DOCS_DIR+'/_build/html')
		open(outputdir+'/.nojekyll', 'wb').close()
	app.connect('build-finished', supportGitHubPages)


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
html_theme = 'sphinx_rtd_theme' # read-the-docs theme looks better than the default "classic" one but has bugs e.g. no table wrapping

html_theme_options = {
	'display_version': True,
	# Toc options
	'collapse_navigation': True,
	'sticky_navigation': True,
	'includehidden': False,
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_context = {'css_files': [
	# Workaround for RTD 0.4.3 bug https://github.com/readthedocs/sphinx_rtd_theme/issues/117
	'_static/theme_overrides.css',  # override wide tables in RTD theme
]}
