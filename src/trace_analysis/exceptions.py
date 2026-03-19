"""Custom exceptions for trace analysis and weakening operations."""


class PropertyValidError(Exception):
    """Raised when the checked property already holds for the model/trace."""


class NoWeakeningError(Exception):
    """Raised when no valid interval weakening can be found."""
