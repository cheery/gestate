"""Gestate autoformatter.

Usage::

    from gestate.fmt import format

    print(format(source_text))
"""

from __future__ import annotations

from .format import format, format_module, format_source

__all__ = ["format", "format_module", "format_source"]
