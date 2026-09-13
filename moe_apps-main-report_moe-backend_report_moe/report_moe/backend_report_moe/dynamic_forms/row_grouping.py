"""Group Info field records into logical table rows (one row = one title submission line)."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Attribute, Info

EMPTY_CELL = "—"


def split_table_textarea_attrs(
    attributes: list[Attribute],
) -> tuple[list[Attribute], list[Attribute]]:
    table_attrs = [a for a in attributes if a.type != "textarea"]
    textarea_attrs = [a for a in attributes if a.type == "textarea"]
    return table_attrs, textarea_attrs


def _empty_row_template(table_attrs: list[Attribute]) -> dict[str, Any]:
    return {f"attr_{a.id}": EMPTY_CELL for a in table_attrs}


def group_table_rows(
    infos: list[Info],
    table_attrs: list[Attribute],
) -> list[dict[str, Any]]:
    """
    Bucket infos into table rows per user (first empty attr slot, else new row).
    Each row dict includes attr_<id>, _info_ids, _commit, _confirm sets.
    """
    if not table_attrs:
        return []

    table_attr_ids = {a.id for a in table_attrs}
    empty = _empty_row_template(table_attrs)
    row_buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for info in infos:
        if info.attribute_id not in table_attr_ids:
            continue
        user_id = info.user_id or 0
        user_rows = row_buckets[user_id]
        target = None
        for row in user_rows:
            if row.get(f"attr_{info.attribute_id}") == EMPTY_CELL:
                target = row
                break
        if target is None:
            target = {
                **empty.copy(),
                "_info_ids": [],
                "_commit": set(),
                "_confirm": set(),
            }
            user_rows.append(target)

        target[f"attr_{info.attribute_id}"] = info.value or EMPTY_CELL
        target["_info_ids"].append(info.id)
        if info.commit_note and info.commit_note.strip():
            target["_commit"].add(info.commit_note.strip())
        if info.confirm_note and info.confirm_note.strip():
            target["_confirm"].add(info.confirm_note.strip())

    built: list[dict[str, Any]] = []
    for user_rows in row_buckets.values():
        built.extend(user_rows)
    return built


def row_is_fully_confirmed(row: dict[str, Any], infos_by_id: dict[int, Info]) -> bool:
    ids = row.get("_info_ids") or []
    if not ids:
        return False
    from .info_confirmation import is_accept

    return all(
        is_accept(infos_by_id[i].confirmed) for i in ids if i in infos_by_id
    )


def count_deduped_table_rows(
    infos: list[Info],
    table_attrs: list[Attribute],
) -> int:
    """Count rows after collapsing identical displayed cell values (matches export)."""
    rows = group_table_rows(infos, table_attrs)
    seen: set[tuple[str, ...]] = set()
    count = 0
    for row in rows:
        key = tuple(row.get(f"attr_{a.id}", EMPTY_CELL) for a in table_attrs)
        if key in seen:
            continue
        seen.add(key)
        count += 1
    return count


def row_stats_for_infos(
    infos: list[Info],
    attributes: list[Attribute],
) -> dict[str, int]:
    """Return total / fully-confirmed / pending deduped table row counts."""
    table_attrs, _ = split_table_textarea_attrs(attributes)
    if not table_attrs:
        return {"rows_count": 0, "rows_confirmed_count": 0, "rows_pending_count": 0}

    infos_by_id = {i.id: i for i in infos}
    rows = group_table_rows(infos, table_attrs)
    seen: set[tuple[str, ...]] = set()
    total = confirmed = 0
    for row in rows:
        key = tuple(row.get(f"attr_{a.id}", EMPTY_CELL) for a in table_attrs)
        if key in seen:
            continue
        seen.add(key)
        total += 1
        if row_is_fully_confirmed(row, infos_by_id):
            confirmed += 1
    pending = max(total - confirmed, 0)
    return {
        "rows_count": total,
        "rows_confirmed_count": confirmed,
        "rows_pending_count": pending,
    }


def aggregate_row_stats_by_title(
    infos: list[Info],
    attributes_by_title: dict[int | None, list[Attribute]],
) -> dict[str, int]:
    """Sum row stats across titles present in infos."""
    by_title: dict[int | None, list[Info]] = defaultdict(list)
    for info in infos:
        title_id = info.attribute.title_id if info.attribute_id else None
        by_title[title_id].append(info)

    totals = {"rows_count": 0, "rows_confirmed_count": 0,
              "rows_pending_count": 0}
    for title_id, title_infos in by_title.items():
        attrs = attributes_by_title.get(title_id, [])
        if not attrs:
            continue
        part = row_stats_for_infos(title_infos, attrs)
        for key in totals:
            totals[key] += part[key]
    return totals


def count_rows_in_queryset(
    qs: QuerySet[Info],
    *,
    title_id: int | None = None,
) -> int:
    """Count logical rows for a filtered queryset (distinct row_key + legacy heuristic)."""
    scoped = qs.filter(
        attribute__title_id=title_id) if title_id is not None else qs
    return count_logical_rows_for_infos_qs(scoped)


def row_stats_via_sql(qs: QuerySet[Info]) -> dict[str, int]:
    """SQL-only equivalent of `row_stats_for_infos`, for querysets too large to
    materialize into Python (e.g. the admin dashboard's unscoped `Info.objects.
    filter(archived=False)` — millions of rows at production scale).

    Row-key'd rows (the normal case since the `(attribute, row_key)` unique
    constraint) are counted with two `GROUP BY row_key` aggregates — a "fully
    confirmed" row is one where every Info in that row_key has `confirmed=accept`.
    Legacy rows with no row_key still need the slot-matching heuristic in
    `count_logical_rows_for_infos_qs`, but that path is only as expensive as the
    (small, non-growing) legacy subset, not the whole table.

    Known divergence from `row_stats_for_infos`: that function additionally
    collapses rows whose *displayed cell values* are identical even across
    different row_keys (`count_deduped_table_rows`'s value-based dedup); this
    function counts by row_key identity only, so two genuinely
    duplicate-content submissions under different row_keys count as two rows
    here but one there. Verified against real data: 3 of 4 sampled titles
    matched exactly, one differed by 1 row out of 55 for exactly this reason.
    Acceptable for a stats display — not acceptable for anything that must be
    exact (that code should keep using the Python path on a scoped queryset).
    """
    from django.db.models import Count, F, Q

    from .info_confirmation import ACCEPT

    keyed = qs.exclude(row_key__isnull=True)
    row_groups = (
        keyed.values('row_key')
        .annotate(
            total=Count('id'),
            confirmed=Count('id', filter=Q(confirmed=ACCEPT)),
        )
    )
    rows_total = row_groups.count()
    rows_confirmed = row_groups.filter(total=F('confirmed')).count()

    null_qs = qs.filter(row_key__isnull=True)
    if null_qs.exists():
        legacy_total = count_logical_rows_for_infos_qs(null_qs)
        # Legacy rows have no per-row confirmed/total split available this
        # cheaply; approximate as unconfirmed (matches the common case: legacy
        # rows predate the confirm workflow). Small, shrinking subset — not
        # worth the full materialization cost to get exact here.
        rows_total += legacy_total

    rows_pending = max(rows_total - rows_confirmed, 0)
    return {
        'rows_count': rows_total,
        'rows_confirmed_count': rows_confirmed,
        'rows_pending_count': rows_pending,
    }


def count_logical_rows_for_infos_qs(qs: QuerySet[Info]) -> int:
    """
    Rows represented by this Info queryset.
    Prefer distinct row_key; legacy rows without row_key use slot grouping per title/sub_main.
    """
    from .models import Attribute

    if not qs.exists():
        return 0

    total = 0
    keyed = qs.exclude(row_key__isnull=True)
    if keyed.exists():
        total += keyed.values("row_key").distinct().count()

    null_qs = qs.filter(row_key__isnull=True)
    if not null_qs.exists():
        return total

    buckets: dict[tuple[int | None, int], list[Info]] = defaultdict(list)
    for info in null_qs.select_related("attribute").iterator(chunk_size=500):
        if not info.attribute_id or not info.sub_main_id:
            continue
        key = (info.attribute.title_id, info.sub_main_id)
        buckets[key].append(info)

    for (tid, _), infos in buckets.items():
        if tid is None:
            continue
        attrs = list(Attribute.objects.filter(title_id=tid))
        table_attrs, _ = split_table_textarea_attrs(attrs)
        total += count_deduped_table_rows(infos, table_attrs)

    return total


def count_export_rows_for_queryset(qs: QuerySet[Info]) -> int:
    """Row count aligned with export buckets: per (title, sub_main)."""
    from .models import Attribute

    buckets: dict[tuple[int | None, int], list[Info]] = defaultdict(list)
    for info in qs.iterator(chunk_size=500):
        if not info.sub_main_id or not info.attribute_id:
            continue
        key = (info.attribute.title_id, info.sub_main_id)
        buckets[key].append(info)

    attrs_cache: dict[int | None, list[Attribute]] = {}
    total = 0
    for (title_id, _), infos in buckets.items():
        if title_id not in attrs_cache:
            attrs = list(Attribute.objects.filter(title_id=title_id))
            table_attrs, _ = split_table_textarea_attrs(attrs)
            attrs_cache[title_id] = table_attrs
        total += count_deduped_table_rows(infos, attrs_cache[title_id])
    return total


def build_title_export_rows(
    infos: list[Info],
    attributes: list[Attribute],
) -> tuple[list[str], list[list[str]], list[dict[str, Any]]]:
    """Build export table headers, cell rows, and narrative blocks."""
    table_attrs, textarea_attrs = split_table_textarea_attrs(attributes)
    textarea_attr_ids = {a.id for a in textarea_attrs}

    grouped = group_table_rows(infos, table_attrs)
    narrative_by_user: dict[int, dict[str, Any]] = {}

    for info in infos:
        if info.attribute_id not in textarea_attr_ids:
            continue
        user_id = info.user_id or 0
        block = narrative_by_user.setdefault(
            user_id,
            {"values": [], "_commit": set(), "_confirm": set()},
        )
        value = (info.value or "").strip()
        if value:
            block["values"].append(info.value)
        if info.commit_note and info.commit_note.strip():
            block["_commit"].add(info.commit_note.strip())
        if info.confirm_note and info.confirm_note.strip():
            block["_confirm"].add(info.confirm_note.strip())

    include_commit = any(row["_commit"] for row in grouped)
    include_confirm = any(row["_confirm"] for row in grouped)

    headers = [a.label for a in table_attrs]
    if include_commit:
        headers.append("ملاحظة الإدخال")
    if include_confirm:
        headers.append("ملاحظة التأكيد")

    rows: list[list[str]] = []
    seen_rows: set[tuple[str, ...]] = set()
    for row in grouped:
        values = [row.get(f"attr_{a.id}", EMPTY_CELL) for a in table_attrs]
        if include_commit:
            values.append(
                " ; ".join(sorted(row["_commit"])
                           ) if row["_commit"] else EMPTY_CELL
            )
        if include_confirm:
            values.append(
                " ; ".join(sorted(row["_confirm"])
                           ) if row["_confirm"] else EMPTY_CELL
            )
        key = tuple(values)
        if key in seen_rows:
            continue
        seen_rows.add(key)
        rows.append(values)

    has_table = bool(table_attrs)
    narratives: list[dict[str, Any]] = []
    for block in narrative_by_user.values():
        if not block["values"] and not block["_commit"] and not block["_confirm"]:
            continue
        unique_values = list(dict.fromkeys(block["values"]))
        entry: dict[str, Any] = {"values": unique_values}
        if not has_table:
            if block["_commit"]:
                entry["commit_note"] = " ; ".join(sorted(block["_commit"]))
            if block["_confirm"]:
                entry["confirm_note"] = " ; ".join(sorted(block["_confirm"]))
        narratives.append(entry)

    return headers, rows, narratives
