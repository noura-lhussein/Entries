"""Utilities for Excel import/export."""

from __future__ import annotations

import re


def norm_text(value: object) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", s)


def cell_value(cell) -> str:
    if cell is None or cell.value is None:
        return ""
    return norm_text(cell.value)
