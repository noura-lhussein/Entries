from __future__ import annotations

import json
from typing import Any


def parse_feature_properties(raw: Any) -> dict[str, Any]:
    """Normalize gis_water_feature.properties (jsonb may arrive as str from psycopg)."""
    current: Any = raw
    for _ in range(3):
        if current is None:
            return {}
        if isinstance(current, dict):
            return current
        if isinstance(current, bytes):
            current = current.decode('utf-8')
            continue
        if isinstance(current, str):
            stripped = current.strip()
            if not stripped:
                return {}
            try:
                current = json.loads(stripped)
            except json.JSONDecodeError:
                return {}
            continue
        return {}
    return current if isinstance(current, dict) else {}
