"""Build logical Info rows (one row = one title submission line per user)."""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .entity_registry import batch_entity_labels, is_entity_attribute, parse_entity_id
from .info_confirmation import ACCEPT, REJECT, WAITING, is_accept, is_reject
from .row_grouping import EMPTY_CELL, group_table_rows, split_table_textarea_attrs

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Attribute, Info


@dataclass
class BuiltInfoRow:
    row_key: str | None
    row_id: str
    user_id: int | None
    user_name: str
    title_id: int | None
    title_name: str | None
    sub_main_id: int | None
    sub_main_name: str | None
    fields: dict[str, str] = field(default_factory=dict)
    info_ids: list[int] = field(default_factory=list)
    confirmed_status: str = WAITING
    confirm_note: str = ""
    commit_note: str = ""
    created_at: str | None = None

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "row_key": str(self.row_key) if self.row_key else None,
            "row_id": self.row_id,
            "user": self.user_id,
            "user_name": self.user_name,
            "title_id": self.title_id,
            "title_name": self.title_name,
            "sub_main_id": self.sub_main_id,
            "sub_main_name": self.sub_main_name,
            "fields": self.fields,
            "info_ids": self.info_ids,
            "confirmed": self.confirmed_status,
            "confirm_note": self.confirm_note or "",
            "commit_note": self.commit_note or "",
            "created_at": self.created_at,
            "_all_accepted": self.confirmed_status == ACCEPT,
            "_all_rejected": self.confirmed_status == REJECT,
            "_all_waiting": self.confirmed_status == WAITING,
        }


def row_confirmed_status(infos: list[Info]) -> str:
    if not infos:
        return WAITING
    if all(is_accept(i.confirmed) for i in infos):
        return ACCEPT
    if all(is_reject(i.confirmed) for i in infos):
        return REJECT
    return WAITING


def _user_display(info: Info) -> str:
    if not info.user_id:
        return "—"
    user = info.user
    if not user:
        return "—"
    return (user.display_name or user.email or "—").strip() or "—"


def _entity_lookups_from_infos(
    infos: list[Info],
    table_attrs: list[Attribute],
) -> dict[str, set[int]]:
    entity_types = {a.id: a.type for a in table_attrs if is_entity_attribute(a.type)}
    by_type: dict[str, set[int]] = defaultdict(set)
    for info in infos:
        attr_type = entity_types.get(info.attribute_id)
        if not attr_type:
            continue
        eid = info.entity_id if info.entity_id is not None else parse_entity_id(info.value)
        if eid is not None and eid > 0:
            by_type[attr_type].add(int(eid))
    return by_type


def _display_field_value(
    *,
    attr: Attribute,
    raw_value: str | None,
    entity_id: int | None,
    label_map: dict[tuple[str, int], str],
) -> str:
    text = (raw_value or "").strip()
    if text == EMPTY_CELL or not text:
        return "—"
    if is_entity_attribute(attr.type):
        eid = entity_id if entity_id is not None else parse_entity_id(text)
        if eid is not None:
            return label_map.get((attr.type, int(eid)), text)
    return text


def _row_from_slot_dict(
    slot: dict[str, Any],
    infos_by_id: dict[int, Info],
    *,
    title_id: int | None,
    title_name: str | None,
    table_attrs: list[Attribute],
    label_map: dict[tuple[str, int], str],
) -> BuiltInfoRow | None:
    info_ids = slot.get("_info_ids") or []
    if not info_ids:
        return None
    sample = infos_by_id.get(info_ids[0])
    if not sample:
        return None

    info_by_attr = {
        infos_by_id[i].attribute_id: infos_by_id[i]
        for i in info_ids
        if i in infos_by_id
    }
    fields: dict[str, str] = {}
    for attr in table_attrs:
        info = info_by_attr.get(attr.id)
        raw = slot.get(f"attr_{attr.id}", EMPTY_CELL)
        fields[str(attr.id)] = _display_field_value(
            attr=attr,
            raw_value=None if raw == EMPTY_CELL else str(raw),
            entity_id=info.entity_id if info is not None else None,
            label_map=label_map,
        )

    commit_notes = slot.get("_commit") or set()
    confirm_notes = slot.get("_confirm") or set()
    row_key = None
    keys = {infos_by_id[i].row_key for i in info_ids if i in infos_by_id}
    keys.discard(None)
    if len(keys) == 1:
        row_key = str(next(iter(keys)))

    status = row_confirmed_status(
        [infos_by_id[i] for i in info_ids if i in infos_by_id]
    )
    created = min(
        (infos_by_id[i].created_at for i in info_ids if i in infos_by_id),
        default=None,
    )

    return BuiltInfoRow(
        row_key=row_key,
        row_id=f"{sample.user_id or 0}-{info_ids[0]}",
        user_id=sample.user_id,
        user_name=_user_display(sample),
        title_id=title_id,
        title_name=title_name,
        sub_main_id=sample.sub_main_id,
        sub_main_name=(
            sample.sub_main.name if sample.sub_main_id and sample.sub_main else None
        ),
        fields=fields,
        info_ids=info_ids,
        confirmed_status=status,
        confirm_note=" ; ".join(sorted(confirm_notes)) if confirm_notes else "",
        commit_note=" ; ".join(sorted(commit_notes)) if commit_notes else "",
        created_at=created.isoformat() if created else None,
    )


def _rows_from_row_key_groups(
    infos: list[Info],
    table_attrs: list[Attribute],
    *,
    title_id: int | None,
    title_name: str | None,
    label_map: dict[tuple[str, int], str],
) -> list[BuiltInfoRow]:
    table_attr_ids = {a.id for a in table_attrs}
    attrs_by_id = {a.id: a for a in table_attrs}
    buckets: dict[uuid.UUID, list[Info]] = defaultdict(list)
    for info in infos:
        if info.row_key:
            buckets[info.row_key].append(info)

    built: list[BuiltInfoRow] = []
    for rk, bucket in buckets.items():
        fields = {str(a.id): "—" for a in table_attrs}
        for info in bucket:
            if info.attribute_id not in table_attr_ids:
                continue
            attr = attrs_by_id[info.attribute_id]
            fields[str(info.attribute_id)] = _display_field_value(
                attr=attr,
                raw_value=info.value,
                entity_id=info.entity_id,
                label_map=label_map,
            )
        info_ids = [i.id for i in bucket]
        sample = bucket[0]
        commit_set = {i.commit_note.strip() for i in bucket if i.commit_note.strip()}
        confirm_set = {i.confirm_note.strip() for i in bucket if i.confirm_note.strip()}
        created = min(i.created_at for i in bucket)
        built.append(
            BuiltInfoRow(
                row_key=str(rk),
                row_id=f"{sample.user_id or 0}-{rk}",
                user_id=sample.user_id,
                user_name=_user_display(sample),
                title_id=title_id,
                title_name=title_name,
                sub_main_id=sample.sub_main_id,
                sub_main_name=(
                    sample.sub_main.name
                    if sample.sub_main_id and sample.sub_main
                    else None
                ),
                fields=fields,
                info_ids=info_ids,
                confirmed_status=row_confirmed_status(bucket),
                confirm_note=" ; ".join(sorted(confirm_set)) if confirm_set else "",
                commit_note=" ; ".join(sorted(commit_set)) if commit_set else "",
                created_at=created.isoformat(),
            )
        )
    return built


def build_rows_for_title_infos(
    infos: list[Info],
    attributes: list[Attribute],
    *,
    title_name: str | None = None,
) -> list[BuiltInfoRow]:
    """Build logical rows for one title's infos."""
    if not infos:
        return []

    title_id = infos[0].attribute.title_id if infos[0].attribute_id else None
    if title_name is None and infos[0].attribute_id and infos[0].attribute:
        title_name = infos[0].attribute.title.name if infos[0].attribute.title_id else None

    table_attrs, _ = split_table_textarea_attrs(attributes)
    if not table_attrs:
        return []

    table_attr_ids = {a.id for a in table_attrs}
    scoped = [i for i in infos if i.attribute_id in table_attr_ids]
    if not scoped:
        return []

    label_map = batch_entity_labels(_entity_lookups_from_infos(scoped, table_attrs))

    use_row_key = scoped and all(i.row_key for i in scoped)
    if use_row_key:
        rows = _rows_from_row_key_groups(
            scoped,
            table_attrs,
            title_id=title_id,
            title_name=title_name,
            label_map=label_map,
        )
    else:
        infos_by_id = {i.id: i for i in scoped}
        slots = group_table_rows(scoped, table_attrs)
        rows = []
        for slot in slots:
            row = _row_from_slot_dict(
                slot,
                infos_by_id,
                title_id=title_id,
                title_name=title_name,
                table_attrs=table_attrs,
                label_map=label_map,
            )
            if row:
                rows.append(row)

    rows.sort(key=lambda r: r.created_at or "", reverse=True)
    return _dedupe_display_rows(rows, table_attrs)


def _dedupe_display_rows(
    rows: list[BuiltInfoRow],
    table_attrs: list[Attribute],
) -> list[BuiltInfoRow]:
    seen: set[tuple[str, ...]] = set()
    out: list[BuiltInfoRow] = []
    for row in rows:
        key = tuple(row.fields.get(str(a.id), "—") for a in table_attrs)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def build_rows_from_infos(infos: list[Info]) -> list[BuiltInfoRow]:
    """Group infos by title and build logical rows."""
    from .models import Attribute

    if not infos:
        return []

    by_title: dict[int | None, list[Info]] = defaultdict(list)
    for info in infos:
        tid = info.attribute.title_id if info.attribute_id else None
        by_title[tid].append(info)

    all_rows: list[BuiltInfoRow] = []
    for title_id, title_infos in by_title.items():
        if title_id is None:
            continue
        attrs = list(Attribute.objects.filter(title_id=title_id))
        all_rows.extend(build_rows_for_title_infos(title_infos, attrs))

    all_rows.sort(key=lambda r: r.created_at or "", reverse=True)
    return all_rows


def filter_rows_by_confirmed(
    rows: list[BuiltInfoRow],
    confirmed: str | None,
) -> list[BuiltInfoRow]:
    if not confirmed:
        return rows
    status = confirmed.strip().lower()
    if status not in (WAITING, ACCEPT, REJECT):
        return rows
    return [r for r in rows if r.confirmed_status == status]


def count_rows_for_queryset(qs: QuerySet[Info]) -> int:
    """Count logical rows for a filtered Info queryset."""
    from .row_grouping import count_logical_rows_for_infos_qs

    return count_logical_rows_for_infos_qs(qs)


def count_rows_with_row_keys(qs: QuerySet[Info], title_id: int) -> int:
    """Fast count when all scoped infos have row_key."""
    scoped = qs.filter(attribute__title_id=title_id)
    if scoped.filter(row_key__isnull=True).exists():
        return count_rows_for_queryset(scoped)
    return scoped.values("row_key").distinct().count()
