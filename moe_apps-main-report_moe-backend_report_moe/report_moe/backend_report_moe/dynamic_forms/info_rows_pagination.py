"""Paginate logical Info rows without materializing the full queryset.

Prefer keyset (cursor) pagination for deep pages. Offset ``page`` remains for
backward compatibility but is slower past the first few pages.
"""

from __future__ import annotations

import base64
import binascii
from datetime import datetime
from typing import Any

from django.db.models import Max, QuerySet
from django.utils.dateparse import parse_datetime

from .info_querysets import INFO_LIST_SELECT_RELATED
from .info_row_builder import BuiltInfoRow, build_rows_from_infos
from .models import Info, InfoRow

LEGACY_MATERIALIZE_CAP = 10000
MAX_PAGE_SIZE = 100
MAX_OFFSET_PAGE = 20  # deep offset pages are expensive; prefer cursor


def clamp_page_args(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
    try:
        p = max(int(page or 1), 1)
    except (TypeError, ValueError):
        p = 1
    try:
        ps = min(max(int(page_size or 20), 1), MAX_PAGE_SIZE)
    except (TypeError, ValueError):
        ps = 20
    return p, ps


def encode_row_cursor(latest: datetime | str, row_key) -> str:
    if hasattr(latest, "isoformat"):
        ts = latest.isoformat()
    else:
        ts = str(latest)
    raw = f"{ts}|{row_key}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_row_cursor(token: str | None) -> tuple[datetime, str] | None:
    if not token or not str(token).strip():
        return None
    pad = "=" * (-len(token) % 4)
    try:
        raw = base64.urlsafe_b64decode(token + pad).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    if "|" not in raw:
        return None
    ts_s, key_s = raw.split("|", 1)
    dt = parse_datetime(ts_s)
    if dt is None or not key_s:
        return None
    return dt, key_s


def _lean_qs(qs: QuerySet[Info]) -> QuerySet[Info]:
    """Drop heavy joins/ordering before aggregation."""
    return qs.order_by().select_related(None)


def _fetch_infos_for_keys(qs: QuerySet[Info], page_keys: list) -> list[Info]:
    return list(
        _lean_qs(qs)
        .filter(row_key__in=page_keys)
        .select_related(*INFO_LIST_SELECT_RELATED)
    )


def _order_built_rows(
    rows: list[BuiltInfoRow],
    page_keys: list,
) -> list[BuiltInfoRow]:
    order = {str(k): i for i, k in enumerate(page_keys)}
    rows.sort(key=lambda r: order.get(str(r.row_key or ""), 10**9))
    return rows


def _keyed_groups(qs: QuerySet[Info]) -> QuerySet:
    """Cell-path grouping: the expensive one. Kept for requests the projection
    cannot answer (attribute_id / free-text search / reject+waiting filters)."""
    return (
        _lean_qs(qs)
        .exclude(row_key__isnull=True)
        .values("row_key")
        .annotate(latest=Max("created_at"))
        .order_by("-latest", "row_key")
    )


def _projection_groups(projection_qs: QuerySet[InfoRow]) -> QuerySet:
    """Same (row_key, latest) shape, read straight off the InfoRow index.

    `-latest_created_at, -row_key` matches dyn_inforow_list_idx, so the page is an
    index range scan instead of a GROUP BY over every cell in the title.
    """
    return projection_qs.order_by("-latest_created_at", "-row_key").values(
        "row_key", "latest_created_at"
    )


def paginate_logical_info_rows(
    qs: QuerySet[Info],
    *,
    page: int,
    page_size: int,
    confirmed: str | None = None,
    cursor: str | None = None,
    include_count: bool = False,
    prefer_keyed: bool = True,
    skip_null_probe: bool = False,
    projection_qs: QuerySet[InfoRow] | None = None,
) -> dict[str, Any]:
    """Return page payload: results, count (optional), next_cursor, flags.

    ``confirmed`` is applied upstream on the queryset (cell filter). Built rows
    are not re-filtered in Python.
    """
    del confirmed  # applied on qs already; kept for call-site clarity
    lean = _lean_qs(qs)

    # The projection already is the grouping, so it needs neither the null-row_key
    # probe (it only ever holds keyed records) nor the aggregate.
    using_projection = projection_qs is not None
    use_keyed = True
    if not using_projection:
        use_keyed = prefer_keyed
        if prefer_keyed and not skip_null_probe:
            use_keyed = not lean.filter(row_key__isnull=True).exists()

    if use_keyed:
        groups = (
            _projection_groups(projection_qs)
            if using_projection
            else _keyed_groups(qs)
        )
        total = groups.count() if include_count else None

        decoded = decode_row_cursor(cursor)
        if decoded is not None:
            import uuid

            from django.db.models import Q

            cur_ts, cur_key = decoded
            try:
                cur_key_uuid = uuid.UUID(str(cur_key))
            except (TypeError, ValueError):
                cur_key_uuid = cur_key
            # Keyset: (latest, row_key) < cursor in DESC order.
            ts_field = "latest_created_at" if using_projection else "latest"
            groups = groups.filter(
                Q(**{f"{ts_field}__lt": cur_ts})
                | Q(**{ts_field: cur_ts, "row_key__lt": cur_key_uuid})
            )
            page_rows_meta = list(groups[:page_size])
        else:
            if page > MAX_OFFSET_PAGE:
                # Refuse pathological deep offsets; clients should use cursor.
                start = (MAX_OFFSET_PAGE - 1) * page_size
                page_rows_meta = list(groups[start: start + page_size])
            else:
                start = (page - 1) * page_size
                page_rows_meta = list(groups[start: start + page_size])

        latest_key = "latest_created_at" if using_projection else "latest"
        page_keys = [r["row_key"] for r in page_rows_meta]
        if not page_keys:
            return {
                "rows": [],
                "count": total if total is not None else 0,
                "count_is_exact": include_count,
                "next_cursor": None,
                "is_truncated": False,
                "used_keyed": True,
            }

        infos = _fetch_infos_for_keys(qs, page_keys)
        rows = _order_built_rows(build_rows_from_infos(infos), page_keys)

        next_cursor = None
        if len(page_rows_meta) == page_size:
            last = page_rows_meta[-1]
            next_cursor = encode_row_cursor(last[latest_key], last["row_key"])

        return {
            "rows": rows,
            "count": total if total is not None else None,
            "count_is_exact": include_count,
            "next_cursor": next_cursor,
            "is_truncated": False,
            "used_keyed": True,
        }

    # Legacy path (any null row_key in scope).
    infos = list(
        lean.select_related(*INFO_LIST_SELECT_RELATED)[:LEGACY_MATERIALIZE_CAP]
    )
    truncated = len(infos) == LEGACY_MATERIALIZE_CAP
    rows = build_rows_from_infos(infos)
    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start: start + page_size]
    next_cursor = None
    return {
        "rows": page_rows,
        "count": total,
        "count_is_exact": True,
        "next_cursor": next_cursor,
        "is_truncated": truncated,
        "used_keyed": False,
    }
