"""
Console output helpers for Windows-friendly script execution.
"""

from __future__ import annotations

import sys


def configure_console_output() -> None:
    """
    Configure stdout/stderr to handle Unicode status messages safely.

    On Windows, scripts can inherit a legacy encoding such as cp1252, which
    causes UnicodeEncodeError when printing emoji or symbols. Reconfigure the
    live streams when possible and otherwise fall back to replacement behavior.
    """

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue

        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")
