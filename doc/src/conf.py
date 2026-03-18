"""Sphinx documentation build configuration."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# pylint: disable=invalid-name

project = "CEGIW"
author = "CEGIW contributors"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "furo"
html_static_path = ["_static"]

# Keep API display concise by hiding the package prefix in rendered docs.
add_module_names = False
modindex_common_prefix = ["src."]
