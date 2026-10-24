"""Shared Sphinx configuration for both languages."""
from pathlib import Path
import sys

DOCS_DIR = Path(__file__).resolve().parent
ROOT_DIR = DOCS_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

project = "image_server"
html_title = "image_server"
root_doc = "index"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
myst_enable_extensions = ["colon_fence", "deflist", "attrs_block", "substitution", "linkify"]
myst_linkify_fuzzy_links = True
myst_heading_anchors = 3
autosummary_generate = True
add_module_names = False
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "private-members": True,
}
autodoc_typehints = "description"
autodoc_preserve_defaults = True
set_type_checking_flag = True
autodoc_mock_imports = ["win32com", "pythoncom", "x_logger", "ese774_frame", "grpc_frame", "grpc"]
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "titles_only": False,
}
exclude_patterns = ["_build"]
