from __future__ import annotations

from datetime import date

project = "Universal Rare-Disease + PGx Analysis Pipeline"
author = "Genomic Analysis Lab"
copyright = f"{date.today().year}, {author}"
release = "1.0.0"
version = release

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_copybutton",
]

autosectionlabel_prefix_document = True
source_suffix = {".rst": "restructuredtext"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_title = project
html_logo = "_static/images/genosphere_logo.png"
html_favicon = "_static/images/genosphere_logo.png"
html_static_path = ["_static"]
html_extra_path = ["_extra"]
html_css_files = ["custom.css"]
html_theme_options = {
    "logo_only": True,
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

copybutton_prompt_text = r"\$ |>>> |\.\.\. "
copybutton_prompt_is_regexp = True

rst_epilog = """
.. |project_name| replace:: Universal Rare-Disease + PGx Analysis Pipeline
"""
