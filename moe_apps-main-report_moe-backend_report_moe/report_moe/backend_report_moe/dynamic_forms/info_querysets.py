from django.db.models import Q

from .info_confirmation import ACCEPT, REJECT, WAITING, normalize_status
from .models import Info, MainSection, SubMainSection

INFO_LIST_SELECT_RELATED = (
    "attribute",
    "attribute__title",
    "sub_main",
    "sub_main__main_section",
    "sub_main__location_district",
    "sub_main__location_district__governorate",
    "loc_governorate",
    "loc_district",
    "loc_subdistrict",
    "loc_community",
    "user",
)


def info_list_base_queryset():
    """Info rows for list/export serializers (avoids N+1 on nested sources)."""
    return Info.objects.select_related(*INFO_LIST_SELECT_RELATED).order_by("-created_at")


def info_count_base_queryset():
    """Same rows as `info_list_base_queryset`, stripped for counting.

    The list version carries 11 `select_related` joins and `order_by("-created_at")`.
    Both are dead weight for a COUNT, and the ordering is worse than dead: Django
    folds a base `order_by` into the GROUP BY of any `.values().annotate()` built
    on top of it, which silently changes what gets counted.
    """
    return Info.objects.all()


def apply_info_archive_filter(qs, query_params):
    """Default: active (non-archived) only. See include_archived / archived_only."""
    archived_only = str(query_params.get("archived_only", "")).lower() in (
        "1",
        "true",
        "yes",
    )
    include_archived = str(query_params.get("include_archived", "")).lower() in (
        "1",
        "true",
        "yes",
    )
    if archived_only:
        return qs.filter(archived=True)
    if include_archived:
        return qs
    return qs.filter(archived=False)


def main_sections_queryset_for_user(user):
    """Admin sees all active; others see parents of assigned sub-sections."""
    if user.is_staff or user.is_superuser:
        return MainSection.objects.filter(deleted=False).order_by("name")
    assigned_main_ids = (
        SubMainSection.objects.filter(
            deleted=False, user_sub_mains__user=user
        )
        .values_list("main_section_id", flat=True)
        .distinct()
    )
    return MainSection.objects.filter(
        deleted=False, id__in=assigned_main_ids
    ).order_by("name")


def ids_from_query_params(query_params, key):
    """Parse repeated or comma-separated query values into a list of int IDs."""
    raw = query_params.getlist(key) if hasattr(query_params, "getlist") else []
    if not raw and query_params.get(key):
        raw = [query_params.get(key)]
    ids = []
    for item in raw:
        for part in str(item).split(","):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
    return ids


def scope_info_queryset_for_user(qs, user):
    if user.is_staff or user.is_superuser:
        return qs
    if user.can_confirm_info or user.can_view_info or user.can_export_reports:
        assigned_sub_mains = list(
            user.user_sub_mains.values_list("sub_main_id", flat=True)
        )
        return qs.filter(sub_main_id__in=assigned_sub_mains)
    return qs.filter(user_id=user.id)


def apply_info_list_filters(qs, query_params):
    p = query_params
    qs = apply_info_archive_filter(qs, p)
    title_ids = ids_from_query_params(p, "title_id")
    title_category_ids = ids_from_query_params(p, "title_category_id")
    attribute_ids = ids_from_query_params(p, "attribute_id")
    main_section_ids = ids_from_query_params(p, "main_section_id")
    sub_main_ids = ids_from_query_params(p, "sub_main_id")
    user_ids = ids_from_query_params(p, "user")
    district_ids = ids_from_query_params(p, "district_id")
    city_ids = ids_from_query_params(p, "city_id")
    governorate_ids = ids_from_query_params(p, "governorate_id")
    community_ids = ids_from_query_params(p, "community_id")
    confirmed = p.get("confirmed")
    date_from = p.get("from")
    date_to = p.get("to")

    if title_category_ids:
        qs = qs.filter(attribute__title__category_id__in=title_category_ids)
    if title_ids:
        # Prefer attribute_id__in over joining attribute→title on every scan.
        from .models import Attribute

        attr_ids = list(
            Attribute.objects.filter(
                title_id__in=title_ids).values_list("id", flat=True)
        )
        qs = qs.filter(attribute_id__in=attr_ids) if attr_ids else qs.none()
    if attribute_ids:
        qs = qs.filter(attribute_id__in=attribute_ids)
    if sub_main_ids:
        qs = qs.filter(sub_main_id__in=sub_main_ids)
    elif main_section_ids:
        qs = qs.filter(sub_main__main_section_id__in=main_section_ids)
    if district_ids:
        qs = qs.filter(
            Q(sub_main__location_district_id__in=district_ids)
            | Q(loc_district_id__in=district_ids)
        )
    elif city_ids or governorate_ids:
        gov_ids = governorate_ids or city_ids
        qs = qs.filter(
            Q(sub_main__location_district__governorate_id__in=gov_ids)
            | Q(loc_governorate_id__in=gov_ids)
        )
    if community_ids:
        qs = qs.filter(loc_community_id__in=community_ids)
    if confirmed:
        status = normalize_status(confirmed, default="")
        if status in (ACCEPT, REJECT, WAITING):
            qs = qs.filter(confirmed=status)
        elif confirmed in ("true", "1", "True"):
            qs = qs.filter(confirmed=ACCEPT)
        elif confirmed in ("false", "0", "False"):
            qs = qs.filter(confirmed=REJECT)
    if user_ids:
        qs = qs.filter(user_id__in=user_ids)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    return qs
