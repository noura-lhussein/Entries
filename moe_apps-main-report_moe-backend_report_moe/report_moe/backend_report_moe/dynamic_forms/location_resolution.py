"""Resolve report attribute values to unified locations FKs + display text."""

from __future__ import annotations

from typing import Any

from locations.models import Community, District, Governorate, SubDistrict

LOCATION_ATTR_TYPES: dict[str, str] = {
    "city": "loc_governorate",
    "district": "loc_district",
    "sub_district": "loc_subdistrict",
    "community": "loc_community",
}


def is_location_attribute(attr_type: str) -> bool:
    return attr_type in LOCATION_ATTR_TYPES


def _norm(value: str) -> str:
    return (value or "").strip().casefold()


def _display_name(obj) -> str:
    return (getattr(obj, "name_ar", None) or getattr(obj, "name_en", None) or str(obj)).strip()


def _match_by_name(candidates, raw: str):
    key = _norm(raw)
    if not key:
        return None
    for item in candidates:
        names = (_norm(getattr(item, "name_ar", "")),
                 _norm(getattr(item, "name_en", "")))
        if key in names:
            return item
    for item in candidates:
        for candidate in (_norm(getattr(item, "name_ar", "")), _norm(getattr(item, "name_en", ""))):
            if candidate and (candidate in key or key in candidate):
                return item
    return None


def _parse_id(raw_value: Any) -> int | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if text.isdigit():
        return int(text)
    return None


def resolve_location_for_attribute(
    attr_type: str,
    raw_value: Any,
    *,
    governorate_id: int | None = None,
    district_id: int | None = None,
    subdistrict_id: int | None = None,
) -> tuple[str, dict[str, int | None]]:
    """Return (display_value, {loc_*_id: ...})."""
    if not is_location_attribute(attr_type):
        return str(raw_value or "").strip(), {}

    loc_kwargs = {
        "loc_governorate_id": None,
        "loc_district_id": None,
        "loc_subdistrict_id": None,
        "loc_community_id": None,
    }
    parsed_id = _parse_id(raw_value)
    raw_text = str(raw_value or "").strip()

    if attr_type == "city":
        gov = Governorate.objects.filter(
            pk=parsed_id).first() if parsed_id else None
        if gov is None and raw_text:
            gov = _match_by_name(Governorate.objects.all(), raw_text)
        if gov:
            loc_kwargs["loc_governorate_id"] = gov.id
            return _display_name(gov), loc_kwargs
        return raw_text, loc_kwargs

    if attr_type == "district":
        qs = District.objects.all()
        if governorate_id:
            qs = qs.filter(governorate_id=governorate_id)
        dist = qs.filter(pk=parsed_id).first() if parsed_id else None
        if dist is None and raw_text:
            dist = _match_by_name(qs, raw_text)
        if dist:
            loc_kwargs["loc_district_id"] = dist.id
            loc_kwargs["loc_governorate_id"] = dist.governorate_id
            return _display_name(dist), loc_kwargs
        return raw_text, loc_kwargs

    if attr_type == "sub_district":
        qs = SubDistrict.objects.all()
        if district_id:
            qs = qs.filter(district_id=district_id)
        sub = qs.filter(pk=parsed_id).first() if parsed_id else None
        if sub is None and raw_text:
            sub = _match_by_name(qs, raw_text)
        if sub:
            loc_kwargs["loc_subdistrict_id"] = sub.id
            loc_kwargs["loc_district_id"] = sub.district_id
            loc_kwargs["loc_governorate_id"] = sub.district.governorate_id
            return _display_name(sub), loc_kwargs
        return raw_text, loc_kwargs

    if attr_type == "community":
        qs = Community.objects.all()
        if subdistrict_id:
            qs = qs.filter(subdistrict_id=subdistrict_id)
        comm = qs.filter(pk=parsed_id).first() if parsed_id else None
        if comm is None and raw_text:
            comm = _match_by_name(qs, raw_text)
        if comm:
            loc_kwargs["loc_community_id"] = comm.id
            loc_kwargs["loc_subdistrict_id"] = comm.subdistrict_id
            loc_kwargs["loc_district_id"] = comm.subdistrict.district_id
            loc_kwargs["loc_governorate_id"] = comm.subdistrict.district.governorate_id
            return _display_name(comm), loc_kwargs
        return raw_text, loc_kwargs

    return raw_text, loc_kwargs


def apply_location_to_info(info, attribute, raw_value: Any, *, context: dict[str, int | None] | None = None):
    """Mutate info.value and loc_* from an attribute + raw submitted/import value."""
    ctx = context or {}
    value, loc_kwargs = resolve_location_for_attribute(
        attribute.type,
        raw_value,
        governorate_id=ctx.get("governorate_id"),
        district_id=ctx.get("district_id"),
        subdistrict_id=ctx.get("subdistrict_id"),
    )
    info.value = value
    for field, pk in loc_kwargs.items():
        setattr(info, field, pk)
    return info


def build_info_records_from_row(
    row_attrs: list[tuple[int, str]],
    attrs_by_id: dict[int, Any],
    *,
    sub_main,
    user,
    row_key,
) -> list:
    """Build Info instances for import/submit with location FK resolution."""
    from .entity_registry import ALL_ENTITY_TYPES, apply_entity_to_info, is_entity_attribute
    from .models import Info

    type_order = {
        **{t: -10 for t in ALL_ENTITY_TYPES},
        "city": 0,
        "district": 1,
        "sub_district": 2,
        "community": 3,
    }
    ordered = sorted(
        row_attrs,
        key=lambda pair: type_order.get(
            getattr(attrs_by_id.get(pair[0]), "type", ""), 99),
    )
    context: dict[str, int | None] = {
        "governorate_id": None,
        "district_id": None,
        "subdistrict_id": None,
    }
    if sub_main and getattr(sub_main, "location_district_id", None):
        context["governorate_id"] = sub_main.location_district.governorate_id

    records = []
    row_entity_type = ""
    row_entity_id: int | None = None
    for attr_id, raw_value in ordered:
        attr = attrs_by_id[attr_id]
        info = Info(
            attribute_id=attr_id,
            sub_main=sub_main,
            user=user,
            row_key=row_key,
            # Denormalised from the attribute; bulk_create skips Info.save().
            is_report_date=attr.is_report_date,
        )
        if is_location_attribute(attr.type):
            apply_location_to_info(info, attr, raw_value, context=context)
            if attr.type == "city" and info.loc_governorate_id:
                context["governorate_id"] = info.loc_governorate_id
            elif attr.type == "district" and info.loc_district_id:
                context["district_id"] = info.loc_district_id
                context["governorate_id"] = info.loc_governorate_id
            elif attr.type == "sub_district" and info.loc_subdistrict_id:
                context["subdistrict_id"] = info.loc_subdistrict_id
                context["district_id"] = info.loc_district_id
        elif is_entity_attribute(attr.type):
            apply_entity_to_info(info, attr, str(raw_value))
            row_entity_type = info.entity_type or row_entity_type
            row_entity_id = info.entity_id or row_entity_id
        else:
            info.value = str(raw_value)
        records.append(info)

    if row_entity_type and row_entity_id:
        for info in records:
            if not info.entity_id:
                info.entity_type = row_entity_type
                info.entity_id = row_entity_id
    return records
