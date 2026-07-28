from __future__ import annotations

import os
from pathlib import Path

project = "Universal Rare-Disease and Pharmacogenomics Analysis Pipeline"
author = "Genomic Analysis Lab"
copyright = "2026, Genomic Analysis Lab"
release = "1.0"
version = "1.0"

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_copybutton",
]

autosectionlabel_prefix_document = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
}
master_doc = "index"

html_theme = "sphinx_rtd_theme"
html_title = "Universal Rare-Disease + PGx Pipeline"
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")
html_short_title = "Rare-Disease + PGx Pipeline"
html_logo = "_static/images/genosphere_logo.png"
html_favicon = "_static/images/genosphere_logo.png"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "style_nav_header_background": "#17324d",
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_context = {
    "display_github": True,
    "github_user": "Wahid-25",
    "github_repo": "rare-disease-genomics-pipeline",
    "github_version": "main",
    "conf_py_path": "/docs/",
}

extlinks = {
    "repo": ("https://github.com/Wahid-25/rare-disease-genomics-pipeline/%s", "%s"),
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

copybutton_prompt_text = r"^\$ |^>>> |^\.\.\. "
copybutton_prompt_is_regexp = True

numfig = True
numfig_format = {
    "figure": "Figure %s",
    "table": "Table %s",
    "code-block": "Listing %s",
}

rst_epilog = """
.. |project_name| replace:: Universal Rare-Disease and Pharmacogenomics Analysis Pipeline
"""
