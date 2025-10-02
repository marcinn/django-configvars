import importlib
import os
import sys
from importlib import metadata
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


project = "django-configvars"
author = "Marcin Nowak"
copyright = "2026, Marcin Nowak"


def _package_version():
    try:
        return metadata.version("django-configvars")
    except metadata.PackageNotFoundError:
        return "dev"


release = os.getenv("DOCS_RELEASE") or _package_version()
version = os.getenv("DOCS_VERSION") or release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

if importlib.util.find_spec("sphinx_copybutton") is not None:
    extensions.append("sphinx_copybutton")

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autosectionlabel_prefix_document = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_mock_imports = ["django"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", None),
}

extlinks = {
    "gh": ("https://github.com/marcinn/django-configvars/%s", "%s"),
}

rst_epilog = f"""
.. |docs_version| replace:: {version}
"""

html_theme = "sphinx_rtd_theme"
if importlib.util.find_spec("sphinx_rtd_theme") is None:
    html_theme = "alabaster"
html_title = f"{project} {version}"
html_short_title = project
html_baseurl = os.getenv("DOCS_BASE_URL", "https://marcinn.github.io/django-configvars/")
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "style_external_links": True,
}
