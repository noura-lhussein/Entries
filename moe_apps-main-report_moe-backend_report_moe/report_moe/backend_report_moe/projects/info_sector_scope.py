"""
Shared TitleCategory → accepted Info helpers for sector dashboards.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Callable

from django.db import DatabaseError

from projects.display_models import (
    ReportDynamicFormsAttribute,
    ReportDynamicFormsInfo,
    ReportDynamicFormsTitle,
    ReportDynamicFormsTitleCategory,
)
from projects.report_forms_read import ACCEPTED

logger = logging.getLogger(__name__)



def _env_int(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=16)
def resolve_title_category_id(
    category_name: str,
    *,
    settings_id: int | None = None,
    env_id_name: str = '',
) -> int | None:
    if settings_id is not None:
        return settings_id
    if env_id_name:
        override = _env_int(env_id_name)
        if override is not None:
            return override
    try:
        row = (
            ReportDynamicFormsTitleCategory.objects
            .filter(name=category_name)
            .order_by('id')
            .first()
        )
    except DatabaseError:
        return None
    return int(row.id) if row else None


def title_ids_for_category(category_id: int | None) -> list[int]:
    if category_id is None:
        return []
    try:
        return list(
            ReportDynamicFormsTitle.objects
            .filter(category_id=category_id, deleted=False)
            .values_list('id', flat=True)
        )
    except DatabaseError:
        return []


def attribute_ids_for_titles(title_ids: list[int]) -> list[int]:
    if not title_ids:
        return []
    try:
        return list(
            ReportDynamicFormsAttribute.objects
            .filter(title_id__in=title_ids)
            .values_list('id', flat=True)
        )
    except DatabaseError:
        return []


def accepted_infos_for_attribute_ids(
    attr_ids: list[int],
    *,
    limit: int = 100000,
) -> list[ReportDynamicFormsInfo]:
    """Fetch accepted Info rows for the given attributes, newest first, capped at
    `limit`. Callers relying on this to represent *all* accepted rows for a
    category (rather than "recent N") should watch the logged warning below —
    silently returning a partial, most-recent-only slice once a sector's Info
    volume passes `limit` is exactly the kind of bug that hid two years of
    rainfall/dam history behind a stale 2009 snapshot until the water dashboards
    were rewritten to query by date instead of by row-count cap."""
    if not attr_ids:
        return []
    try:
        qs = ReportDynamicFormsInfo.objects.filter(
            confirmed=ACCEPTED,
            attribute_id__in=attr_ids,
        )
        # Prefer non-archived when column exists on mirror.
        if hasattr(ReportDynamicFormsInfo, 'archived'):
            qs = qs.filter(archived=False)
        rows = list(qs.order_by('-created_at', '-id')[:limit])
        if len(rows) == limit:
            logger.warning(
                'accepted_infos_for_attribute_ids: hit limit=%d for %d attribute ids — '
                'results are truncated to the most recent rows; older accepted Info for '
                'this category is silently invisible to callers. Raise `limit` or switch '
                'this caller to a date-scoped query (see water/info_dashboard.py).',
                limit, len(attr_ids),
            )
        return rows
    except DatabaseError:
        return []


def accepted_infos_for_category(
    category_name: str,
    *,
    settings_id: int | None = None,
    env_id_name: str = '',
    limit: int = 100000,
) -> list[ReportDynamicFormsInfo]:
    cid = resolve_title_category_id(
        category_name, settings_id=settings_id, env_id_name=env_id_name
    )
    title_ids = title_ids_for_category(cid)
    attr_ids = attribute_ids_for_titles(title_ids)
    return accepted_infos_for_attribute_ids(attr_ids, limit=limit)


def clear_title_category_cache() -> None:
    resolve_title_category_id.cache_clear()


def make_sector_scope(
    category_name: str,
    *,
    env_id_name: str,
    settings_getter: Callable[[], int | None] | None = None,
):
    """Tiny namespace helper used by sector info_scope modules."""

    def category_id() -> int | None:
        sid = settings_getter() if settings_getter else None
        return resolve_title_category_id(
            category_name, settings_id=sid, env_id_name=env_id_name
        )

    def infos(*, limit: int = 20000) -> list[ReportDynamicFormsInfo]:
        return accepted_infos_for_category(
            category_name,
            settings_id=settings_getter() if settings_getter else None,
            env_id_name=env_id_name,
            limit=limit,
        )

    return category_id, infos
