"""Sector daily-report packs: Title.code lists only — never Attribute fields.

Field lists always come from ``importable_attributes`` for each member title.
"""

from __future__ import annotations

from typing import Any

ELECTRICITY_DAILY_PACK: dict[str, Any] = {
    "root": "electricity.national",
    "members": [
        "electricity.national",
        "electricity.governorate_load_entity",
        "electricity.hydro_dam_entity",
        "electricity.unit_entity",
        "electricity.generation_incident",
        "electricity.grid_incident",
        "electricity.daily_notes",
    ],
}

OIL_GAS_DAILY_PACK: dict[str, Any] = {
    "root": "oil_gas.national",
    "members": [
        "oil_gas.national",
        "oil_gas.field_entity",
        "oil_gas.refinery_entity",
    ],
}

_PACKS_BY_ROOT = {
    ELECTRICITY_DAILY_PACK["root"]: ELECTRICITY_DAILY_PACK,
    OIL_GAS_DAILY_PACK["root"]: OIL_GAS_DAILY_PACK,
}


def pack_for_title_code(code: str) -> dict[str, Any] | None:
    code = (code or "").strip()
    if not code:
        return None
    return _PACKS_BY_ROOT.get(code)
