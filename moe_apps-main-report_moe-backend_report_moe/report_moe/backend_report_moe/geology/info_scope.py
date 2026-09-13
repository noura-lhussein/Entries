"""Geology Info scope via TitleCategory «إدارة قطاع التعدين»."""

from __future__ import annotations

import os

from django.conf import settings
from projects.info_sector_scope import (
    accepted_infos_for_attribute_ids,
    attribute_ids_for_titles,
    clear_title_category_cache,
    resolve_title_category_id,
    title_ids_for_category,
)

# Canonical name matches water / electricity / petroleum: «إدارة قطاع …».
GEOLOGY_TITLE_CATEGORY_NAME = 'إدارة قطاع التعدين'
GEOLOGY_TITLE_CATEGORY_ALIASES = (
    GEOLOGY_TITLE_CATEGORY_NAME,
    'إدارة الجيولوجيا',
)


def geology_category_name() -> str:
    return getattr(settings, 'GEOLOGY_TITLE_CATEGORY_NAME', None) or GEOLOGY_TITLE_CATEGORY_NAME


def geology_category_id_override() -> int | None:
    raw = getattr(settings, 'GEOLOGY_TITLE_CATEGORY_ID', None) or os.getenv(
        'GEOLOGY_TITLE_CATEGORY_ID'
    )
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def resolve_geology_category_id() -> int | None:
    override = geology_category_id_override()
    if override is not None:
        return override
    names = [geology_category_name(), *GEOLOGY_TITLE_CATEGORY_ALIASES]
    seen: set[str] = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        cid = resolve_title_category_id(
            name,
            env_id_name='GEOLOGY_TITLE_CATEGORY_ID',
        )
        if cid is not None:
            return cid
    return None


def accepted_infos_for_geology_category(*, limit: int = 100000):
    cid = resolve_geology_category_id()
    title_ids = title_ids_for_category(cid)
    attr_ids = attribute_ids_for_titles(title_ids)
    return accepted_infos_for_attribute_ids(attr_ids, limit=limit)


def clear_geology_scope_cache() -> None:
    clear_title_category_cache()
