"""
Resolve oil & gas Info scope via TitleCategory «إدارة قطاع البترول».
"""

from __future__ import annotations

import os

from django.conf import settings
from projects.info_sector_scope import (
    accepted_infos_for_category,
    clear_title_category_cache,
    resolve_title_category_id,
)

OIL_GAS_TITLE_CATEGORY_NAME = 'إدارة قطاع البترول'


def oil_gas_category_name() -> str:
    return getattr(settings, 'OIL_GAS_TITLE_CATEGORY_NAME', None) or OIL_GAS_TITLE_CATEGORY_NAME


def oil_gas_category_id_override() -> int | None:
    raw = getattr(settings, 'OIL_GAS_TITLE_CATEGORY_ID', None) or os.getenv(
        'OIL_GAS_TITLE_CATEGORY_ID'
    )
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def resolve_oil_gas_category_id() -> int | None:
    return resolve_title_category_id(
        oil_gas_category_name(),
        settings_id=oil_gas_category_id_override(),
        env_id_name='OIL_GAS_TITLE_CATEGORY_ID',
    )


def accepted_infos_for_oil_gas_category(*, limit: int = 100000):
    return accepted_infos_for_category(
        oil_gas_category_name(),
        settings_id=oil_gas_category_id_override(),
        env_id_name='OIL_GAS_TITLE_CATEGORY_ID',
        limit=limit,
    )


def clear_oil_gas_scope_cache() -> None:
    clear_title_category_cache()
