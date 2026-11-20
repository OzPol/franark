from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
project = "Franark"
author = "Franark contributors"
release = "0.1.0"
extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.napoleon"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
html_title = "Franark documentation"
html_static_path = ["_static"]
html_theme_options = {"description": "Local agent workflows with traceable results"}
myst_enable_extensions = ["colon_fence", "dollarmath"]
nitpicky = False
