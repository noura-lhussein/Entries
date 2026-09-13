"""
Resolve electricity Info scope via TitleCategory «إدارة قطاع الكهرباء».
Thin wrapper over projects.info_sector_scope.
"""

from __future__ import annotations

import os

from django.conf import settings
from projects.display_models import ReportDynamicFormsInfo
from projects.info_sector_scope import (
    accepted_infos_for_category,
    attribute_ids_for_titles,
    clear_title_category_cache,
    resolve_title_category_id,
    title_ids_for_category,
)

ELECTRICITY_TITLE_CATEGORY_NAME = 'إدارة قطاع الكهرباء'


def electricity_category_name() -> str:
    return getattr(settings, 'ELECTRICITY_TITLE_CATEGORY_NAME', None) or ELECTRICITY_TITLE_CATEGORY_NAME


def electricity_category_id_override() -> int | None:
    raw = getattr(settings, 'ELECTRICITY_TITLE_CATEGORY_ID', None) or os.getenv(
        'ELECTRICITY_TITLE_CATEGORY_ID'
    )
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def resolve_electricity_category_id() -> int | None:
    return resolve_title_category_id(
        electricity_category_name(),
        settings_id=electricity_category_id_override(),
        env_id_name='ELECTRICITY_TITLE_CATEGORY_ID',
    )


def electricity_title_ids(*, category_id: int | None = None) -> list[int]:
    cid = category_id if category_id is not None else resolve_electricity_category_id()
    return title_ids_for_category(cid)


def electricity_attribute_ids(*, category_id: int | None = None) -> list[int]:
    return attribute_ids_for_titles(electricity_title_ids(category_id=category_id))


def accepted_infos_for_electricity_category(*, limit: int = 100000) -> list[ReportDynamicFormsInfo]:
    """Accepted Info rows whose attributes belong to electricity TitleCategory."""
    return accepted_infos_for_category(
        electricity_category_name(),
        settings_id=electricity_category_id_override(),
        env_id_name='ELECTRICITY_TITLE_CATEGORY_ID',
        limit=limit,
    )


def clear_electricity_scope_cache() -> None:
    clear_title_category_cache()
