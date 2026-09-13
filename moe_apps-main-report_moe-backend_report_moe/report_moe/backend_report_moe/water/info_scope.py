"""Water Info scope via TitleCategory «إدارة قطاع المياه»."""

from __future__ import annotations

import os

from django.conf import settings
from projects.info_sector_scope import (
    accepted_infos_for_category,
    clear_title_category_cache,
    resolve_title_category_id,
)

WATER_TITLE_CATEGORY_NAME = 'إدارة قطاع المياه'


def water_category_name() -> str:
    return getattr(settings, 'WATER_TITLE_CATEGORY_NAME', None) or WATER_TITLE_CATEGORY_NAME


def water_category_id_override() -> int | None:
    raw = getattr(settings, 'WATER_TITLE_CATEGORY_ID', None) or os.getenv(
        'WATER_TITLE_CATEGORY_ID'
    )
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def resolve_water_category_id() -> int | None:
    return resolve_title_category_id(
        water_category_name(),
        settings_id=water_category_id_override(),
        env_id_name='WATER_TITLE_CATEGORY_ID',
    )


def accepted_infos_for_water_category(*, limit: int = 20000):
    return accepted_infos_for_category(
        water_category_name(),
        settings_id=water_category_id_override(),
        env_id_name='WATER_TITLE_CATEGORY_ID',
        limit=limit,
    )


def clear_water_scope_cache() -> None:
    clear_title_category_cache()
