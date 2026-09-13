from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..info_querysets import (
    apply_info_list_filters,
    scope_info_queryset_for_user,
)
from ..info_row_querysets import (
    apply_info_row_filters,
    info_row_base_queryset,
    scope_info_rows_for_user,
)
from ..info_rows_pagination import clamp_page_args, paginate_logical_info_rows
from ..models import Info
from ..permissions import CanWriteInfo

# Above this many matching Info rows, a query with no narrowing filter is refused.
UNSCOPED_QUERY_GUARD_THRESHOLD = 50000

_NARROWING_PARAMS = (
    "title_id", "title_category_id", "attribute_id",
    "main_section_id", "sub_main_id", "from", "to",
)


def _truthy(raw) -> bool:
    return str(raw or "").strip().lower() in ("1", "true", "yes")


class InfoRowsListView(APIView):
    """
    List logical Info rows (grouped by title + user + row_key/slots).
    Same filters as GET /infos/.

    Pagination:
    - Prefer ``cursor`` (keyset) for load-more / deep pages.
    - ``page`` offset still works for early pages (slower when deep).
    - ``include_count=1`` forces a total count; first offset page counts by default.
    """

    permission_classes = [CanWriteInfo]

    def get(self, request):
        # Lean base — select_related applied only when fetching the page Infos.
        qs = Info.objects.all()
        qs = scope_info_queryset_for_user(qs, request.user)
        qs = apply_info_list_filters(qs, request.query_params)

        search = (request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(value__icontains=search) | Q(
                    attribute__label__icontains=search)
            )

        is_narrowed = any(request.query_params.get(p)
                          for p in _NARROWING_PARAMS)
        if not is_narrowed:
            total = qs.count()
            if total > UNSCOPED_QUERY_GUARD_THRESHOLD:
                return Response(
                    {
                        "detail": (
                            f"هذا الاستعلام يطابق {total} صفاً بلا أي فلتر تضييق — "
                            "حدّد title_id أو نطاقاً زمنياً (from/to) أولاً."
                        ),
                        "total_unfiltered": total,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        page, page_size = clamp_page_args(
            request.query_params.get("page"),
            request.query_params.get("page_size"),
        )
        cursor = (request.query_params.get("cursor") or "").strip() or None
        include_count = _truthy(request.query_params.get("include_count"))
        if (
            not cursor
            and page == 1
            and request.query_params.get("include_count") is None
        ):
            include_count = True

        # Title-scoped lists are almost always fully row-keyed; skip the null probe.
        prefer_keyed = True
        skip_null_probe = bool(request.query_params.get("title_id"))

        # Prefer the materialized logical-row projection: it turns the page from a
        # GROUP BY + MAX(created_at) over every cell in the title into an ordered
        # index scan (1.68 s -> 0.6 ms on the largest title). It cannot express
        # cell-level predicates, so those requests keep the aggregate path.
        projection_qs, projectable = apply_info_row_filters(
            scope_info_rows_for_user(info_row_base_queryset(), request.user),
            request.query_params,
        )

        payload = paginate_logical_info_rows(
            qs,
            page=page,
            page_size=page_size,
            confirmed=request.query_params.get("confirmed"),
            cursor=cursor,
            include_count=include_count,
            prefer_keyed=prefer_keyed,
            skip_null_probe=skip_null_probe,
            projection_qs=projection_qs if projectable else None,
        )

        return Response(
            {
                "count": payload["count"],
                "count_is_exact": payload["count_is_exact"],
                "is_truncated": payload["is_truncated"],
                "page": page,
                "page_size": page_size,
                "next_cursor": payload["next_cursor"],
                "results": [r.to_api_dict() for r in payload["rows"]],
            }
        )
