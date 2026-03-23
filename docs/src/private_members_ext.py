"""Sphinx extension to automatically add private members documentation sections."""

import importlib
import inspect
import re


def source_read(_app, docname, source):
    """Inject private members documentation sections after automodule directives."""
    if not docname.startswith("_api/src."):
        return
    text = source[0]
    # Skip if already has private members section
    if "Private Members" in text:
        return
    # Find automodule directives
    pattern = r"(.. automodule:: ([^\n]+)\n(?:   :[^\n]+\n)*)"

    def _private_functions(module_name: str) -> list[str]:
        """Return sorted private function names defined in a module."""
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return []
        private_names = []
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_") or name.startswith("__"):
                continue
            if getattr(obj, "__module__", None) != module_name:
                continue
            private_names.append(name)
        return sorted(private_names)

    def replace_with_private_section(match):
        full_match = match.group(1)
        module_name = match.group(2).strip()
        private_members = _private_functions(module_name)
        # Check if this is the first automodule (public section)
        before_match = text[: match.start()]
        if "Private Members" in before_match:
            return full_match
        if not private_members:
            return full_match
        private_items = "\n\n".join(
            [
                f".. autofunction:: {module_name}.{name}\n" "   :no-index:"
                for name in private_members
            ],
        )
        # Add private members section after the first (public) automodule
        private_section = (
            f"{full_match}\n\n"
            f"Private Members\n"
            f"^^^^^^^^^^^^^^^\n\n"
            f"{private_items}\n"
        )
        return private_section

    # Only replace the first occurrence
    new_text = re.sub(pattern, replace_with_private_section, text, count=1)
    source[0] = new_text


def setup(app):
    """Register the extension."""
    app.connect("source-read", source_read)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
