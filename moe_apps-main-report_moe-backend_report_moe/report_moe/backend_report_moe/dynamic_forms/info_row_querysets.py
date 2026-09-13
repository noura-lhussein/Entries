"""Translate the Info list filters onto the InfoRow projection.

`apply_info_list_filters` filters *cells*; the list endpoints then group those
cells into logical rows. The projection already is that grouping, so the same
request can be answered by filtering it directly — no aggregation, and the
ordering comes off an index.

Not every filter survives the translation. `attribute_id`, free-text `search` and
the reject/waiting statuses are properties of individual cells, not of the record,
so those requests keep using the cell path. `projectable=False` is the signal to
fall back; it is never a silent approximation.

Do NOT try to bridge the two by semi-joining the projection against a filtered
cell queryset (`InfoRow.objects.filter(row_key__in=cells.values("row_key"))`).
Measured: 5.3 s against 1.7 s for the plain aggregate — the planner loses the
ordered index scan and falls back to a sequential scan of the projection with a
nested-loop probe per row.
"""

from django.db.models import Q

from .info_confirmation import ACCEPT, REJECT, WAITING, normalize_status
from .info_querysets import ids_from_query_params
from .models import InfoRow, SubMainSection


def info_row_base_queryset():
    return InfoRow.objects.all()


def scope_info_rows_for_user(qs, user):
    """Mirror of `scope_info_queryset_for_user` against the projection."""
    if user.is_staff or user.is_superuser:
        return qs
    if user.can_confirm_info or user.can_view_info or user.can_export_reports:
        assigned_sub_mains = list(
            user.user_sub_mains.values_list("sub_main_id", flat=True)
        )
        return qs.filter(sub_main_id__in=assigned_sub_mains)
    return qs.filter(user_id=user.id)


def _truthy(raw) -> bool:
    return str(raw or "").strip().lower() in ("1", "true", "yes")


def _sub_mains_in_district(district_ids):
    """SubMainSection is a 26-row table; resolving it in Python keeps the
    projection free of a denormalised location_district_id column."""
    return list(
        SubMainSection.objects.filter(
            location_district_id__in=district_ids
        ).values_list("id", flat=True)
    )


def _sub_mains_in_governorate(gov_ids):
    return list(
        SubMainSection.objects.filter(
            location_district__governorate_id__in=gov_ids
        ).values_list("id", flat=True)
    )


def apply_info_row_filters(qs, query_params) -> tuple[object, bool]:
    """Returns ``(queryset, projectable)``.

    When ``projectable`` is False the queryset is meaningless — the caller must
    run the cell path instead.
    """
    p = query_params

    # Cell-level predicates the projection cannot express.
    if ids_from_query_params(p, "attribute_id"):
        return qs, False
    if (p.get("search") or "").strip():
        return qs, False

    confirmed = p.get("confirmed")
    if confirmed:
        status = normalize_status(confirmed, default="")
        if status in (REJECT, WAITING) or confirmed in ("false", "0", "False"):
            # "has a rejected cell" is not a record-level fact.
            return qs, False
        if status == ACCEPT or confirmed in ("true", "1", "True"):
            qs = qs.filter(accepted_count__gt=0)

    # archived / include_archived / archived_only
    if _truthy(p.get("archived_only")):
        qs = qs.filter(archived=True)
    elif not _truthy(p.get("include_archived")):
        qs = qs.filter(archived=False)

    title_ids = ids_from_query_params(p, "title_id")
    if title_ids:
        qs = qs.filter(title_id__in=title_ids)

    title_category_ids = ids_from_query_params(p, "title_category_id")
    if title_category_ids:
        qs = qs.filter(title_category_id__in=title_category_ids)

    sub_main_ids = ids_from_query_params(p, "sub_main_id")
    main_section_ids = ids_from_query_params(p, "main_section_id")
    if sub_main_ids:
        qs = qs.filter(sub_main_id__in=sub_main_ids)
    elif main_section_ids:
        qs = qs.filter(main_section_id__in=main_section_ids)

    district_ids = ids_from_query_params(p, "district_id")
    city_ids = ids_from_query_params(p, "city_id")
    governorate_ids = ids_from_query_params(p, "governorate_id")
    if district_ids:
        qs = qs.filter(
            Q(sub_main_id__in=_sub_mains_in_district(district_ids))
            | Q(loc_district_id__in=district_ids)
        )
    elif city_ids or governorate_ids:
        gov_ids = governorate_ids or city_ids
        qs = qs.filter(
            Q(sub_main_id__in=_sub_mains_in_governorate(gov_ids))
            | Q(loc_governorate_id__in=gov_ids)
        )

    community_ids = ids_from_query_params(p, "community_id")
    if community_ids:
        qs = qs.filter(loc_community_id__in=community_ids)

    user_ids = ids_from_query_params(p, "user")
    if user_ids:
        qs = qs.filter(user_id__in=user_ids)

    # A record matches a date window when its cells overlap it. Cells of a record
    # are written together, so first/latest bracket the same instant in practice.
    date_from = p.get("from")
    date_to = p.get("to")
    if date_from:
        qs = qs.filter(latest_created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(first_created_at__date__lte=date_to)

    return qs, True
