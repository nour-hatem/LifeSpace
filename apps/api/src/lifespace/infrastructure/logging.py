"""Logging configuration built on the standard library only.

This module configures process-wide logging and is safe to call more than once.
It must not import the API layer, and it never logs request bodies or
credentials.
"""

import logging


def configure_logging(level: str) -> None:
    """Configure the root logger once, updating the level on later calls."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        root.addHandler(handler)
