"""Resolve SubMainSection from Excel section columns."""

from __future__ import annotations

from locations.models import District as LocationDistrict

from ..models import MainSection, SubMainSection
from .constants import (
    COL_GOVERNORATE,
    COL_LOCATION,
    COL_MAIN_SECTION,
    COL_REGION,
    COL_SUB_MAIN,
)
from .exceptions import ImportRowError


def region_from_row_values(values: dict[str, str]) -> str:
    return (
        values.get(COL_REGION, "")
        or values.get(COL_GOVERNORATE, "")
        or values.get(COL_LOCATION, "")
    )


def _assert_sub_main_allowed(user, sub_main: SubMainSection, row: int) -> None:
    if user.is_staff or user.is_superuser:
        return
    allowed = user.user_sub_mains.filter(sub_main_id=sub_main.id).exists()
    if not allowed:
        raise ImportRowError(
            row,
            f"ليس لديك صلاحية على القسم الفرعي: {sub_main.name}",
        )


def resolve_sub_main_for_import(
    values: dict[str, str],
    user,
    row: int,
    *,
    sub_main_id: int | None = None,
) -> SubMainSection:
    base_qs = SubMainSection.objects.select_related(
        "main_section", "location_district"
    )

    # Preferred path: UI already selected main/sub — do not read them from Excel.
    if sub_main_id is not None:
        sub_main = base_qs.filter(pk=sub_main_id).first()
        if not sub_main:
            raise ImportRowError(row, "القسم الفرعي المحدد غير موجود.")
        _assert_sub_main_allowed(user, sub_main, row)
        return sub_main

    main_name = values.get(COL_MAIN_SECTION, "")
    sub_name = values.get(COL_SUB_MAIN, "")
    region = region_from_row_values(values)

    sub_main = None

    if sub_name and main_name:
        sub_main = base_qs.filter(
            name=sub_name, main_section__name=main_name
        ).first()
    if not sub_main and sub_name:
        sub_main = base_qs.filter(name=sub_name).first()
        if not sub_main:
            sub_main = base_qs.filter(name__iexact=sub_name).first()

    if not sub_main and region:
        loc_dist = LocationDistrict.objects.filter(name_ar=region).first()
        if not loc_dist:
            loc_dist = LocationDistrict.objects.filter(
                name_ar__iexact=region).first()
        if not loc_dist:
            loc_dist = LocationDistrict.objects.filter(name_en=region).first()
        if loc_dist:
            qs = base_qs.filter(location_district_id=loc_dist.id)
            if main_name:
                qs = qs.filter(main_section__name=main_name)
            sub_main = qs.order_by("id").first()

    if not sub_main and main_name and not sub_name:
        main = MainSection.objects.filter(name=main_name).first()
        if not main:
            main = MainSection.objects.filter(
                name__icontains=main_name[:40]
            ).first()
        if main:
            subs = base_qs.filter(main_section_id=main.id)
            if subs.count() == 1:
                sub_main = subs.first()
            elif region:
                loc_dist = LocationDistrict.objects.filter(
                    name_ar=region).first()
                if loc_dist:
                    sub_main = subs.filter(
                        location_district_id=loc_dist.id).first()

    if not sub_main:
        raise ImportRowError(
            row,
            "تعذر تحديد القسم الفرعي: أدخل القسم الفرعي أو المنطقة/المحافظة "
            "المطابقة لقاعدة البيانات",
        )

    _assert_sub_main_allowed(user, sub_main, row)
    return sub_main
