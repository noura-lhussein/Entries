"""Custom (non-ViewSet) OpenAPI paths: auth, reports, GIS, sectors, master-data."""

from __future__ import annotations

from typing import Any

from .openapi import (
    COMMON_ERRORS,
    PAGE_PARAMS,
    info_filter_params,
    json_content,
    op,
    path_param,
    q,
    ref,
    responses,
)


def tags() -> list[dict[str, str]]:
    return [
        {"name": "Auth", "description": "CSRF, login, session, current user."},
        {"name": "Users", "description": "Users and assignment tables."},
        {"name": "Form builder", "description": "Sections, titles, attributes, options."},
        {"name": "Reports", "description": "Submit Info, form schema, Excel import."},
        {"name": "Info", "description": "Accepted / pending Info rows and confirmation."},
        {"name": "Budget", "description": "Project budget module."},
        {"name": "Locations", "description": "Governorates, districts, communities."},
        {"name": "Master data", "description": "Shared catalogs (slug-based CRUD)."},
        {"name": "GIS", "description": "Admin boundaries and sector GeoJSON."},
        {"name": "Datasets", "description": "Portal dataset catalogue (writes → 410)."},
        {"name": "Projects", "description": "Portal projects (writes → 410)."},
        {"name": "Geology", "description": "Mining dashboard, ore export, admin registry."},
        {"name": "Electricity", "description": "Grid dashboard, reports, targets, map."},
        {"name": "Petroleum", "description": "Oil dashboard, reports, targets, map."},
        {"name": "Water", "description": "Rainfall, dams, Euphrates, drinking water."},
    ]


def _ok(schema: dict[str, Any] | None = None, description: str = "OK") -> dict[str, Any]:
    extra: dict[str, Any] = {"200": {"description": description}}
    if schema is not None:
        extra["200"]["content"] = json_content(schema)
    return extra


def _file(description: str = "File download") -> dict[str, Any]:
    return {
        "200": {
            "description": description,
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"}
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"}
                },
                "application/pdf": {
                    "schema": {"type": "string", "format": "binary"}
                },
            },
        }
    }


def _multipart(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return {
        "required": True,
        "content": {"multipart/form-data": {"schema": schema}},
    }


def _json_body(schema: dict[str, Any]) -> dict[str, Any]:
    return {"required": True, "content": json_content(schema)}


AREA_FILTERS = [
    q("governorate"),
    q("district"),
    q("subdistrict"),
]

ADMIN_GEO_FILTERS = AREA_FILTERS + [
    q("adm0_pcode"),
    q("adm1_pcode"),
    q("adm2_pcode"),
    q("adm3_pcode"),
    q("pcode"),
]

DRINKING_FILTERS = [
    q("governorate"),
    q("district"),
    q("subdistrict"),
    q("org_unit"),
    q("community"),
    q("search"),
    q("enrollment_year", typ="integer"),
    q("station_working"),
    q("boosting_station"),
    q("well_station"),
    q("filtration_station"),
    q("needs_solar_power"),
    q("grid_power"),
    q("previously_rehabilitated"),
    q("public_grid_supply"),
    q("grid_connection_working"),
    q("solar_power_available"),
    q("alternative_power_source"),
    q("needs_solar_installation"),
    q("solar_space_available"),
    q("safety_procedures", enum=["no", "partially", "yes"]),
    q("electrical_connection_efficiency", enum=["1", "2", "3"]),
]

DATE_Q = q("date", required=True, format="date", description="YYYY-MM-DD.")
FORMAT_XLSX_PDF = q(
    "format",
    enum=["xlsx", "pdf", "excel", "xls"],
    default="xlsx",
    description="File type. Not a DRF renderer name.",
)


def _admin_crud(prefix: str, tag: str) -> dict[str, Any]:
    slug = path_param("slug", typ="string", description="Registry resource slug.")
    pk = path_param("pk", typ="string", description="Primary key.")
    return {
        f"{prefix}/admin/registry/": {
            "get": op(
                summary="Admin resource registry",
                tags=[tag],
                responses=responses("401", "403", extra=_ok(ref("AdminRegistry"))),
            )
        },
        f"{prefix}/admin/{{slug}}/options/": {
            "get": op(
                summary="Admin dropdown options",
                tags=[tag],
                parameters=[slug],
                responses=responses(
                    "401", "403", "404", extra=_ok(ref("AdminOptions"))
                ),
            )
        },
        f"{prefix}/admin/{{slug}}/": {
            "get": op(
                summary="List admin resource rows",
                tags=[tag],
                parameters=[
                    slug,
                    q("search"),
                    q("page", typ="integer"),
                    q("page_size", typ="integer"),
                    q("sort"),
                    q("direction", enum=["asc", "desc"]),
                ],
                responses=responses(
                    "401", "403", "404", extra=_ok(ref("AdminList"))
                ),
            ),
            "post": op(
                summary="Create admin resource row",
                tags=[tag],
                description="Body is the resource's model fields (see registry schema). GIS / read-only slugs return 405.",
                parameters=[slug],
                request_body=_json_body(
                    {"type": "object", "additionalProperties": True}
                ),
                responses=responses(
                    "400",
                    "401",
                    "403",
                    "404",
                    extra={
                        "201": {
                            "description": "Created",
                            "content": json_content({"type": "object"}),
                        },
                        "405": COMMON_ERRORS["403"] | {"description": "Read-only or GIS write blocked"},
                    },
                ),
            ),
        },
        f"{prefix}/admin/{{slug}}/{{pk}}/": {
            "get": op(
                summary="Retrieve admin resource row",
                tags=[tag],
                parameters=[slug, pk],
                responses=responses(
                    "401", "403", "404", extra=_ok({"type": "object"})
                ),
            ),
            "patch": op(
                summary="Partial update admin resource row",
                tags=[tag],
                parameters=[slug, pk],
                request_body=_json_body(
                    {"type": "object", "additionalProperties": True}
                ),
                responses=responses(
                    "400",
                    "401",
                    "403",
                    "404",
                    extra=_ok({"type": "object"}) | {"405": {"description": "Read-only"}},
                ),
            ),
            "delete": op(
                summary="Delete admin resource row",
                tags=[tag],
                parameters=[slug, pk],
                responses=responses(
                    "401",
                    "403",
                    "404",
                    extra={"204": {"description": "Deleted"}, "405": {"description": "Read-only"}},
                ),
            ),
        },
    }


def _facts(path: str, tag: str, summary: str, pk: str, pk_type: str = "integer") -> dict[str, Any]:
    return {
        path: {
            "get": op(
                summary=summary,
                tags=[tag],
                parameters=[path_param(pk, typ=pk_type)],
                responses=responses(
                    "401", "403", "404", extra=_ok(ref("EntityFacts"))
                ),
            )
        }
    }


def _gone_post(path: str, tag: str, summary: str) -> dict[str, Any]:
    return {
        path: {
            "post": op(
                summary=summary,
                tags=[tag],
                description="Always 410. Enter data through Form Builder / Info.",
                request_body=_json_body({"type": "object", "additionalProperties": True}),
                responses=responses("401", "403", "410"),
            )
        }
    }


def custom_paths() -> dict[str, Any]:
    paths: dict[str, Any] = {}

    # ── Auth ────────────────────────────────────────────────────────────────
    paths["/api/v1/auth/csrf/"] = {
        "get": op(
            summary="Get CSRF token",
            tags=["Auth"],
            description="Sets the `csrftoken` cookie and returns it in JSON. Public.",
            security=[],
            responses=responses(extra=_ok(ref("CsrfToken"))),
        )
    }
    paths["/api/v1/auth/login/"] = {
        "post": op(
            summary="Log in",
            tags=["Auth"],
            description="Public. Rate-limited (5/min). 5 failures lock the identifier for 15 minutes.",
            security=[],
            request_body=_json_body(ref("LoginRequest")),
            responses=responses(
                "400",
                "429",
                extra=_ok(ref("User"), "Logged-in user"),
            ),
        )
    }
    paths["/api/v1/auth/logout/"] = {
        "post": op(
            summary="Log out",
            tags=["Auth"],
            responses=responses(
                "401",
                extra=_ok(
                    {
                        "type": "object",
                        "properties": {"detail": {"type": "string", "example": "Logged out"}},
                    }
                ),
            ),
        )
    }
    paths["/api/v1/auth/me/"] = {
        "get": op(
            summary="Current user",
            tags=["Auth"],
            description="Also sets the CSRF cookie for returning sessions.",
            responses=responses("401", extra=_ok(ref("User"))),
        )
    }
    paths["/api/v1/auth/permissions/"] = {
        "get": op(
            summary="Current user permissions",
            tags=["Auth"],
            description="Same payload as `/auth/me/`.",
            responses=responses("401", extra=_ok(ref("User"))),
        )
    }
    paths["/api/v1/user/main-sections/"] = {
        "get": op(
            summary="Main sections visible to the current user",
            tags=["Auth"],
            responses=responses(
                "401",
                extra=_ok(
                    {
                        "type": "object",
                        "properties": {
                            "is_admin": {"type": "boolean"},
                            "main_sections": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                    },
                                },
                            },
                        },
                    }
                ),
            ),
        )
    }
    paths["/api/v1/dashboard/stats/"] = {
        "get": op(
            summary="Admin dashboard stats",
            tags=["Info"],
            description="Admin-only counts, confirmation rates, recent audit activity.",
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }

    # ── Uploads ─────────────────────────────────────────────────────────────
    paths["/api/v1/uploads/limits/"] = {
        "get": op(
            summary="Upload size limit",
            tags=["Reports"],
            responses=responses(
                "401",
                extra=_ok(
                    {
                        "type": "object",
                        "properties": {"max_upload_bytes": {"type": "integer"}},
                    }
                ),
            ),
        )
    }
    paths["/api/v1/uploads/form-file/"] = {
        "post": op(
            summary="Upload a form file",
            tags=["Reports"],
            description="Stores under MEDIA_ROOT. Put the returned URL in Info.value.",
            request_body=_multipart(
                {
                    "file": {"type": "string", "format": "binary"},
                    "kind": {"type": "string", "enum": ["image", "file"], "default": "file"},
                },
                ["file"],
            ),
            responses=responses(
                "400",
                "401",
                "403",
                extra=_ok(ref("FileUploadResult")),
            ),
        )
    }

    # ── Report submit / schema ──────────────────────────────────────────────
    paths["/api/v1/reports/submit/"] = {
        "post": op(
            summary="Submit one title's attribute values",
            tags=["Reports"],
            request_body=_json_body(ref("SubmitReportRequest")),
            responses=responses(
                "400",
                "401",
                "403",
                "409",
                extra=_ok(ref("SubmitReportResponse")),
            ),
        )
    }
    paths["/api/v1/reports/submit-full/"] = {
        "post": op(
            summary="Submit several titles in one request",
            tags=["Reports"],
            request_body=_json_body(ref("SubmitFullReportRequest")),
            responses=responses(
                "400",
                "401",
                "403",
                "409",
                extra=_ok(ref("SubmitReportResponse")),
            ),
        )
    }
    paths["/api/v1/reports/check-date/"] = {
        "get": op(
            summary="Check duplicate report date",
            tags=["Reports"],
            parameters=[
                q("title_id", typ="integer", required=True),
                q("sub_main_id", typ="integer", required=True),
                q("date", required=True, format="date"),
                q("entity_type"),
                q("entity_id", typ="integer"),
            ],
            responses=responses(
                "400",
                "401",
                "403",
                extra=_ok(
                    {
                        "type": "object",
                        "properties": {
                            "duplicate": {"type": "boolean"},
                            "date": {"type": "string"},
                        },
                    }
                ),
            ),
        )
    }
    paths["/api/v1/reports/full-structure/"] = {
        "get": op(
            summary="Full form structure",
            tags=["Reports"],
            parameters=[q("title_id", typ="integer")],
            responses=responses("401", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/reports/form-schema/"] = {
        "get": op(
            summary="Form schema for a title",
            tags=["Reports"],
            parameters=[q("title_id", typ="integer", required=True)],
            responses=responses("400", "401", extra=_ok({"type": "object"})),
        )
    }

    # ── Export reports (confirmed Info) ─────────────────────────────────────
    export_filters = info_filter_params() + [
        q(
            "export_format",
            enum=["xlsx", "excel", "docx", "word", "pdf"],
            description="If set, downloads a file instead of listing rows.",
        ),
        q("full_report", description="Include full report layout when exporting."),
    ]
    paths["/api/v1/export-reports/"] = {
        "get": op(
            summary="List or download confirmed Info rows",
            tags=["Reports"],
            parameters=PAGE_PARAMS + export_filters,
            responses=responses(
                "400",
                "401",
                "403",
                extra={
                    **_ok({"type": "object"}, "Paginated rows when export_format is omitted"),
                    **_file("Excel / Word / PDF when export_format is set"),
                },
            ),
        )
    }
    paths["/api/v1/export-reports/download/"] = {
        "get": op(
            summary="Download confirmed Info export",
            tags=["Reports"],
            parameters=export_filters,
            responses=responses("400", "401", "403", extra=_file()),
        )
    }

    # ── Info extras ─────────────────────────────────────────────────────────
    paths["/api/v1/infos/row-count/"] = {
        "get": op(
            summary="Count Info rows for a title",
            tags=["Info"],
            parameters=info_filter_params() + [q("title_id", typ="integer")],
            responses=responses("401", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/info-rows/"] = {
        "get": op(
            summary="Logical Info rows (grouped)",
            tags=["Info"],
            description="Requires a narrowing filter if the unscoped match exceeds 50k rows.",
            parameters=PAGE_PARAMS + info_filter_params() + [q("search")],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/infos/{id}/detail/"] = {
        "get": op(
            summary="Info row detail (rich)",
            tags=["Info"],
            parameters=[path_param("id")],
            responses=responses("401", "404", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/infos/{id}/toggle_confirmed/"] = {
        "post": op(
            summary="Toggle or set confirmation on one Info field",
            tags=["Info"],
            parameters=[path_param("id")],
            request_body=_json_body(
                {
                    "type": "object",
                    "properties": {
                        "confirmed": {"type": "boolean"},
                        "status": {"type": "string"},
                        "note": {"type": "string"},
                    },
                }
            ),
            responses=responses("401", "403", "404", extra=_ok(ref("InfoRow"))),
        )
    }
    for action, body_props, resp_props in (
        (
            "bulk-confirm",
            {"note": {"type": "string"}},
            {"confirmed": {"type": "integer"}, "updated_rows": {"type": "integer"}},
        ),
        (
            "bulk-reject",
            {"note": {"type": "string"}},
            {"rejected": {"type": "integer"}, "updated_rows": {"type": "integer"}},
        ),
        (
            "confirm-ids",
            {
                "ids": {"type": "array", "items": {"type": "integer"}},
                "status": {"type": "string"},
                "note": {"type": "string"},
            },
            {"updated": {"type": "integer"}, "updated_rows": {"type": "integer"}},
        ),
        (
            "confirm-row-keys",
            {
                "row_keys": {"type": "array", "items": {"type": "string"}},
                "status": {"type": "string"},
                "note": {"type": "string"},
            },
            {"updated": {"type": "integer"}, "updated_rows": {"type": "integer"}},
        ),
        (
            "commit-note-ids",
            {
                "ids": {"type": "array", "items": {"type": "integer"}},
                "note": {"type": "string"},
            },
            {"updated": {"type": "integer"}},
        ),
    ):
        paths[f"/api/v1/infos/{action}/"] = {
            "post": op(
                summary=action.replace("-", " ").title(),
                tags=["Info"],
                description="Uses the same list filters as GET /infos/ to scope the queryset (except confirm-ids / row-keys).",
                request_body=_json_body({"type": "object", "properties": body_props}),
                responses=responses(
                    "401",
                    "403",
                    extra=_ok({"type": "object", "properties": resp_props}),
                ),
            )
        }

    paths["/api/v1/geocode/search/"] = {
        "get": op(
            summary="Geocode search",
            tags=["Locations"],
            parameters=[q("q", required=True, description="Place name.")],
            responses=responses("400", "401", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/entity-options/{entity_type}/"] = {
        "get": op(
            summary="Entity typeahead options",
            tags=["Master data"],
            parameters=[
                path_param("entity_type", typ="string"),
                q("q", description="Search text."),
                q("limit", typ="integer", default=100),
            ],
            responses=responses("401", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }

    # Form-builder extras
    paths["/api/v1/sub-sections/tree/"] = {
        "get": op(
            summary="Nested sub-section tree",
            tags=["Form builder"],
            parameters=[q("main_section", typ="integer", required=True)],
            responses=responses(
                "400",
                "401",
                extra=_ok({"type": "array", "items": {"type": "object"}}),
            ),
        )
    }
    paths["/api/v1/sub-sections/{id}/assigned-users/"] = {
        "get": op(
            summary="Users assigned to a sub-section",
            tags=["Form builder"],
            parameters=[path_param("id")],
            responses=responses(
                "401", "403", "404", extra=_ok({"type": "array", "items": {"type": "object"}})
            ),
        )
    }
    paths["/api/v1/titles/{id}/assigned-users/"] = {
        "get": op(
            summary="Users assigned to a title (via category)",
            tags=["Form builder"],
            parameters=[path_param("id")],
            responses=responses(
                "401", "403", "404", extra=_ok({"type": "array", "items": {"type": "object"}})
            ),
        )
    }
    paths["/api/v1/titles/{id}/excel-template/"] = {
        "get": op(
            summary="Download Excel template for a title",
            tags=["Reports"],
            parameters=[
                path_param("id"),
                q("layout", enum=["measures", "wide"], description="Sheet layout."),
                q("sub_main_id", typ="integer"),
            ],
            responses=responses("400", "401", "403", "404", extra=_file("xlsx")),
        )
    }
    paths["/api/v1/titles/{id}/excel-import/"] = {
        "post": op(
            summary="Import Excel into Info for a title",
            tags=["Reports"],
            parameters=[
                path_param("id"),
                q("dry_run", description="1/true = validate only."),
                q("sub_main_id", typ="integer"),
            ],
            request_body=_multipart(
                {
                    "file": {"type": "string", "format": "binary"},
                    "sub_main_id": {"type": "integer"},
                },
                ["file"],
            ),
            responses=responses("400", "401", "403", "404", extra=_ok({"type": "object"})),
        )
    }

    # Budget extras
    paths["/api/v1/budget/projects/dashboard/"] = {
        "get": op(
            summary="Budget project dashboard",
            tags=["Budget"],
            parameters=[q("status"), q("year", typ="integer")],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/budget/projects/map-points/"] = {
        "get": op(
            summary="Budget project map points",
            tags=["Budget"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/budget/projects/eligible-previous/"] = {
        "get": op(
            summary="Eligible previous-year projects",
            tags=["Budget"],
            parameters=[
                q("annual_budget", typ="integer", required=True),
                q("exclude", typ="integer"),
            ],
            responses=responses(
                "400",
                "401",
                "403",
                extra=_ok({"type": "array", "items": {"type": "object"}}),
            ),
        )
    }
    paths["/api/v1/budget/projects/{id}/assignments/"] = {
        "get": op(
            summary="List users assigned to a budget project",
            tags=["Budget"],
            parameters=[path_param("id")],
            responses=responses("401", "403", "404", extra=_ok({"type": "array", "items": {"type": "object"}})),
        ),
        "post": op(
            summary="Assign a user to a budget project",
            tags=["Budget"],
            parameters=[path_param("id")],
            request_body=_json_body(
                {
                    "type": "object",
                    "required": ["user_id"],
                    "properties": {"user_id": {"type": "integer"}},
                }
            ),
            responses=responses("400", "401", "403", "404", extra={"201": {"description": "Created", "content": json_content({"type": "object"})}}),
        ),
    }
    paths["/api/v1/budget/projects/{id}/assignments/{user_id}/"] = {
        "delete": op(
            summary="Remove a project assignment",
            tags=["Budget"],
            parameters=[path_param("id"), path_param("user_id")],
            responses=responses("401", "403", extra={"204": {"description": "Deleted"}, "404": COMMON_ERRORS["404"]}),
        )
    }
    paths["/api/v1/budget/projects/{id}/change-log/"] = {
        "get": op(
            summary="Change log for one budget project",
            tags=["Budget"],
            parameters=[path_param("id")] + PAGE_PARAMS,
            responses=responses("401", "403", "404", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/budget/users/{id}/assignments/"] = {
        "get": op(
            summary="Budget user project assignments",
            tags=["Budget"],
            parameters=[path_param("id")],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        ),
        "put": op(
            summary="Replace budget user project assignments",
            tags=["Budget"],
            parameters=[path_param("id")],
            request_body=_json_body({"type": "object", "additionalProperties": True}),
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        ),
    }

    # ── Master data ─────────────────────────────────────────────────────────
    paths["/api/v1/master-data/registry/"] = {
        "get": op(
            summary="Master-data registry",
            tags=["Master data"],
            responses=responses("401", "403", extra=_ok(ref("AdminRegistry"))),
        )
    }
    paths["/api/v1/master-data/by-entity/{entity_type}/"] = {
        "get": op(
            summary="Resolve master-data slug by entity type",
            tags=["Master data"],
            parameters=[path_param("entity_type", typ="string")],
            responses=responses("401", "403", "404", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/master-data/{slug}/options/"] = {
        "get": op(
            summary="Master-data dropdown options",
            tags=["Master data"],
            parameters=[path_param("slug", typ="string")],
            responses=responses("401", "403", "404", extra=_ok(ref("AdminOptions"))),
        )
    }
    paths["/api/v1/master-data/{slug}/"] = {
        "get": op(
            summary="List master-data rows",
            tags=["Master data"],
            parameters=[
                path_param("slug", typ="string"),
                q("search"),
                q("status"),
                q("sort"),
                q("direction", enum=["asc", "desc"], default="asc"),
                q("page", typ="integer", default=1),
                q("page_size", typ="integer", default=50),
            ],
            responses=responses("401", "403", "404", extra=_ok(ref("AdminList"))),
        ),
        "post": op(
            summary="Create master-data row",
            tags=["Master data"],
            parameters=[path_param("slug", typ="string")],
            request_body=_json_body({"type": "object", "additionalProperties": True}),
            responses=responses(
                "400",
                "401",
                "403",
                "404",
                "409",
                extra={"201": {"description": "Created", "content": json_content({"type": "object"})}},
            ),
        ),
    }
    paths["/api/v1/master-data/{slug}/{pk}/"] = {
        "get": op(
            summary="Retrieve master-data row",
            tags=["Master data"],
            parameters=[path_param("slug", typ="string"), path_param("pk", typ="string")],
            responses=responses("401", "403", "404", extra=_ok({"type": "object"})),
        ),
        "patch": op(
            summary="Update master-data row",
            tags=["Master data"],
            parameters=[path_param("slug", typ="string"), path_param("pk", typ="string")],
            request_body=_json_body({"type": "object", "additionalProperties": True}),
            responses=responses("400", "401", "403", "404", "409", extra=_ok({"type": "object"})),
        ),
        "delete": op(
            summary="Delete master-data row",
            tags=["Master data"],
            parameters=[path_param("slug", typ="string"), path_param("pk", typ="string")],
            responses=responses(
                "401",
                "403",
                "409",
                extra={"204": {"description": "Deleted"}, "404": COMMON_ERRORS["404"]},
            ),
        ),
    }

    # ── GIS ─────────────────────────────────────────────────────────────────
    paths["/api/v1/gis/admin-layers/"] = {
        "get": op(
            summary="Admin boundary layer catalog",
            tags=["GIS"],
            responses=responses("401", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/gis/admin-layers/{layer_id}/geojson/"] = {
        "get": op(
            summary="Admin boundary GeoJSON",
            tags=["GIS"],
            parameters=[path_param("layer_id", typ="string")] + ADMIN_GEO_FILTERS,
            responses=responses("401", "404", extra=_ok(ref("GeoJSONFeatureCollection"))),
        )
    }
    paths["/api/v1/gis/filters/{filter_key}/"] = {
        "get": op(
            summary="Filter option values",
            tags=["GIS"],
            parameters=[
                path_param("filter_key", typ="string", description="governorate | district | subdistrict"),
                q("governorate"),
                q("district"),
            ],
            responses=responses("401", "404", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/gis/water-layers/"] = {
        "get": op(
            summary="Water layer catalog",
            tags=["GIS"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/gis/water-layers/{layer_id}/geojson/"] = {
        "get": op(
            summary="Water layer GeoJSON",
            tags=["GIS"],
            parameters=[path_param("layer_id", typ="string")] + AREA_FILTERS,
            responses=responses("401", "403", "404", extra=_ok(ref("GeoJSONFeatureCollection"))),
        )
    }
    paths["/api/v1/gis/springs/map-catalog/"] = {
        "get": op(
            summary="Springs map catalog",
            tags=["GIS"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/gis/geology-layers/"] = {
        "get": op(
            summary="Geology / mining layer catalog",
            tags=["GIS"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/gis/geology-layers/{layer_id}/geojson/"] = {
        "get": op(
            summary="Geology layer GeoJSON",
            tags=["GIS"],
            parameters=[path_param("layer_id", typ="string")] + AREA_FILTERS,
            responses=responses("401", "403", "404", extra=_ok(ref("GeoJSONFeatureCollection"))),
        )
    }
    paths["/api/v1/gis/geology-info/"] = {
        "get": op(
            summary="Geology info catalog (map cards)",
            tags=["GIS"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }

    # ── Datasets ────────────────────────────────────────────────────────────
    paths["/api/v1/datasets/"] = {
        "get": op(
            summary="List datasets",
            tags=["Datasets"],
            parameters=[
                q("search"),
                q("format"),
                q("organization"),
                q("sector", description="oil-gas | water-resources | electricity | mineral-resources"),
                q("governorate"),
                q("status"),
                q("include_inactive", description="1 = include inactive."),
                q("ordering", default="-updated_at"),
                q("page", typ="integer", default=1),
                q("page_size", typ="integer", default=10),
            ],
            responses=responses("400", "401", extra=_ok({"type": "object"})),
        ),
        "post": op(
            summary="Create dataset (retired)",
            tags=["Datasets"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "410"),
        ),
    }
    paths["/api/v1/datasets/meta/"] = {
        "get": op(
            summary="Dataset filter metadata",
            tags=["Datasets"],
            parameters=[q("sector"), q("status"), q("governorate"), q("format")],
            responses=responses("400", "401", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/datasets/{pk}/"] = {
        "get": op(
            summary="Retrieve dataset",
            tags=["Datasets"],
            parameters=[
                path_param("pk"),
                q("track_view", description="1 = increment view count."),
            ],
            responses=responses("401", "404", extra=_ok({"type": "object"})),
        ),
        "patch": op(
            summary="Update dataset (retired)",
            tags=["Datasets"],
            parameters=[path_param("pk")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "410"),
        ),
        "delete": op(
            summary="Delete dataset (retired)",
            tags=["Datasets"],
            parameters=[path_param("pk")],
            responses=responses("401", "410"),
        ),
    }
    paths["/api/v1/datasets/{pk}/download/"] = {
        "get": op(
            summary="Download dataset file",
            tags=["Datasets"],
            parameters=[path_param("pk"), q("resource_id", typ="integer")],
            responses=responses("400", "401", "404", extra=_file()),
        )
    }
    paths["/api/v1/datasets/{pk}/preview/"] = {
        "get": op(
            summary="Preview dataset file (inline)",
            tags=["Datasets"],
            parameters=[path_param("pk"), q("resource_id", typ="integer")],
            responses=responses("401", "404", extra=_file("inline file")),
        )
    }
    paths["/api/v1/datasets/{pk}/spatial-layers/"] = {
        "get": op(
            summary="Shapefile → GeoJSON slices",
            tags=["Datasets"],
            parameters=[path_param("pk"), q("resource_id", typ="integer")],
            responses=responses(
                "400",
                "401",
                "404",
                extra=_ok(
                    {
                        "type": "object",
                        "properties": {"slices": {"type": "array", "items": {"type": "object"}}},
                    }
                ),
            ),
        )
    }
    paths["/api/v1/datasets/{pk}/record-download/"] = {
        "post": op(
            summary="Increment download counter",
            tags=["Datasets"],
            parameters=[path_param("pk")],
            responses=responses(
                "401",
                "404",
                extra=_ok(
                    {
                        "type": "object",
                        "properties": {"download_count": {"type": "integer"}},
                    }
                ),
            ),
        )
    }

    # ── Portal projects ─────────────────────────────────────────────────────
    sector_q = q(
        "sector",
        description="oil-gas | water-resources | electricity | mineral-resources",
    )
    paths["/api/v1/projects/"] = {
        "get": op(
            summary="List portal projects",
            tags=["Projects"],
            parameters=[sector_q, q("include_inactive", description="1 = include inactive.")],
            responses=responses("400", "401", extra=_ok({"type": "array", "items": {"type": "object"}})),
        ),
        "post": op(
            summary="Create project (retired)",
            tags=["Projects"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "410"),
        ),
    }
    paths["/api/v1/projects/meta/"] = {
        "get": op(
            summary="Project filter metadata",
            tags=["Projects"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/projects/summary/"] = {
        "get": op(
            summary="Projects summary",
            tags=["Projects"],
            parameters=[sector_q],
            responses=responses("400", "401", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/projects/dashboard/"] = {
        "get": op(
            summary="Projects dashboard",
            tags=["Projects"],
            parameters=[q("sector", required=True)],
            responses=responses("400", "401", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/projects/organizations/"] = {
        "get": op(
            summary="List organizations",
            tags=["Projects"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        ),
        "post": op(
            summary="Create organization (retired)",
            tags=["Projects"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
    }
    paths["/api/v1/projects/organizations/{pk}/"] = {
        "get": op(
            summary="Retrieve organization",
            tags=["Projects"],
            parameters=[path_param("pk")],
            responses=responses("401", "403", "404", extra=_ok({"type": "object"})),
        ),
        "patch": op(
            summary="Update organization (retired)",
            tags=["Projects"],
            parameters=[path_param("pk")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
        "delete": op(
            summary="Delete organization (retired)",
            tags=["Projects"],
            parameters=[path_param("pk")],
            responses=responses("401", "403", "410"),
        ),
    }
    paths["/api/v1/projects/{pk}/"] = {
        "get": op(
            summary="Retrieve portal project",
            tags=["Projects"],
            parameters=[path_param("pk")],
            responses=responses("401", "404", extra=_ok({"type": "object"})),
        ),
        "patch": op(
            summary="Update project (retired)",
            tags=["Projects"],
            parameters=[path_param("pk")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "410"),
        ),
        "delete": op(
            summary="Delete project (retired)",
            tags=["Projects"],
            parameters=[path_param("pk")],
            responses=responses("401", "410"),
        ),
    }
    paths["/api/v1/projects/{pk}/monitoring/"] = {
        "get": op(
            summary="Project monitoring (retired)",
            tags=["Projects"],
            parameters=[path_param("pk")],
            responses=responses("401", "410"),
        ),
        "put": op(
            summary="Update monitoring (retired)",
            tags=["Projects"],
            parameters=[path_param("pk")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "410"),
        ),
    }

    # ── Geology ─────────────────────────────────────────────────────────────
    paths["/api/v1/geology/dashboard/"] = {
        "get": op(
            summary="Mining dashboard",
            tags=["Geology"],
            parameters=[q("plan_year", typ="integer", example=2026)],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/geology/reports/export/"] = {
        "get": op(
            summary="Export ore-production report",
            tags=["Geology"],
            parameters=[
                q("plan_year", typ="integer", example=2026),
                FORMAT_XLSX_PDF,
            ],
            responses=responses("400", "401", "403", "404", extra=_file()),
        )
    }
    paths["/api/v1/geology/admin/daily-report/"] = {
        "get": op(
            summary="Read geology daily report row",
            tags=["Geology"],
            parameters=[q("report_date", required=True, format="date")],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        ),
        "post": op(
            summary="Write daily report (retired)",
            tags=["Geology"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
    }
    paths["/api/v1/geology/admin/daily-report/template/"] = {
        "get": op(
            summary="Daily-report template (retired)",
            tags=["Geology"],
            responses=responses("401", "403", "410"),
        )
    }
    paths["/api/v1/geology/admin/daily-report/export/"] = {
        "get": op(
            summary="Legacy daily-report export (retired)",
            tags=["Geology"],
            description="Use GET /api/v1/geology/reports/export/ instead.",
            responses=responses("401", "403", "410"),
        )
    }
    paths["/api/v1/geology/admin/daily-report/import/"] = {
        "post": op(
            summary="Daily-report import (retired)",
            tags=["Geology"],
            request_body=_multipart({"file": {"type": "string", "format": "binary"}}, ["file"]),
            responses=responses("401", "403", "410"),
        )
    }
    paths.update(_admin_crud("/api/v1/geology", "Geology"))

    # ── Electricity ─────────────────────────────────────────────────────────
    paths["/api/v1/electricity/info-catalog/"] = {
        "get": op(
            summary="Electricity Info catalog (Data page)",
            tags=["Electricity"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/electricity/dashboard/"] = {
        "get": op(
            summary="Electricity dashboard",
            tags=["Electricity"],
            parameters=[
                q("period", enum=["day", "month"], default="day"),
                q("date", format="date", description="For period=day."),
                q("month", description="YYYY-MM for period=month."),
            ],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/electricity/trends/{metric_key}/"] = {
        "get": op(
            summary="Electricity metric trend",
            tags=["Electricity"],
            parameters=[
                path_param("metric_key", typ="string"),
                q("days", typ="integer", default=30),
                q("date", format="date", description="End date."),
            ],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths.update(_sector_reports("/api/v1/electricity", "Electricity"))
    paths["/api/v1/electricity/map-layers/{layer_id}/geojson/"] = {
        "get": op(
            summary="Electricity map layer GeoJSON",
            tags=["Electricity"],
            parameters=[path_param("layer_id", typ="string")] + AREA_FILTERS,
            responses=responses("401", "403", "404", extra=_ok(ref("GeoJSONFeatureCollection"))),
        )
    }
    paths["/api/v1/electricity/master/power-plants/"] = {
        "get": op(
            summary="Power plant catalogue",
            tags=["Electricity"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths.update(
        _facts(
            "/api/v1/electricity/power-plants/{plant_id}/report-facts/",
            "Electricity",
            "Power plant + Info facts",
            "plant_id",
        )
    )
    paths.update(
        _facts(
            "/api/v1/electricity/substations/{substation_id}/report-facts/",
            "Electricity",
            "Substation + Info facts",
            "substation_id",
        )
    )
    paths.update(
        _facts(
            "/api/v1/electricity/transmission-lines/{line_id}/report-facts/",
            "Electricity",
            "Transmission line + Info facts",
            "line_id",
        )
    )
    for feat, label in (
        ("gis-substations-66", "66 kV GIS substation"),
        ("gis-substations-230", "230 kV GIS substation"),
        ("gis-substations-400", "400 kV GIS substation"),
        ("gis-renewable-sites", "Renewable site"),
    ):
        paths.update(
            _facts(
                f"/api/v1/electricity/{feat}/{{feature_id}}/report-facts/",
                "Electricity",
                f"{label} + Info facts",
                "feature_id",
            )
        )
    paths.update(_gone_post("/api/v1/electricity/operations/daily/", "Electricity", "Daily operations upsert (retired)"))
    paths.update(_gone_post("/api/v1/electricity/operations/publish/", "Electricity", "Daily operations publish (retired)"))
    paths["/api/v1/electricity/targets/catalog/"] = {
        "get": op(
            summary="Electricity target metric catalog",
            tags=["Electricity"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/electricity/targets/coverage/"] = {
        "get": op(
            summary="Electricity target coverage",
            tags=["Electricity"],
            parameters=[DATE_Q],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/electricity/targets/plants/"] = {
        "get": op(
            summary="Plant target matrix (generation_mwh)",
            tags=["Electricity"],
            parameters=[DATE_Q],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/electricity/targets/monthly/"] = {
        "get": op(
            summary="Monthly target rollup",
            tags=["Electricity"],
            parameters=[DATE_Q, q("scope_type"), q("scope_code")],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths.update(_admin_crud("/api/v1/electricity", "Electricity"))

    # ── Petroleum ───────────────────────────────────────────────────────────
    paths["/api/v1/oil-gas/dashboard/"] = {
        "get": op(
            summary="Petroleum dashboard",
            tags=["Petroleum"],
            parameters=[
                q("period", enum=["day", "month"], default="day"),
                q("date", format="date"),
                q("month", description="YYYY-MM for period=month."),
            ],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/oil-gas/trends/{metric_key}/"] = {
        "get": op(
            summary="Petroleum metric trend",
            tags=["Petroleum"],
            parameters=[
                path_param("metric_key", typ="string"),
                q("days", typ="integer", default=30),
                q("date", format="date"),
            ],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths.update(_sector_reports("/api/v1/oil-gas", "Petroleum"))
    paths["/api/v1/oil-gas/map-layers/{layer_id}/geojson/"] = {
        "get": op(
            summary="Petroleum map layer GeoJSON",
            tags=["Petroleum"],
            parameters=[path_param("layer_id", typ="string")] + AREA_FILTERS,
            responses=responses("401", "403", "404", extra=_ok(ref("GeoJSONFeatureCollection"))),
        )
    }
    paths["/api/v1/oil-gas/master/facilities/"] = {
        "get": op(
            summary="Facilities catalogue",
            tags=["Petroleum"],
            parameters=[q("sector"), q("facility_type")],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/oil-gas/master/refineries/"] = {
        "get": op(
            summary="Refineries catalogue",
            tags=["Petroleum"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/oil-gas/master/fields/"] = {
        "get": op(
            summary="Oil fields catalogue",
            tags=["Petroleum"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        ),
        "post": op(
            summary="Create field (retired)",
            tags=["Petroleum"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
    }
    paths["/api/v1/oil-gas/master/fields/{code}/"] = {
        "get": op(
            summary="Retrieve oil field",
            tags=["Petroleum"],
            parameters=[path_param("code", typ="string")],
            responses=responses("401", "403", "404", extra=_ok({"type": "object"})),
        ),
        "patch": op(
            summary="Update field (retired)",
            tags=["Petroleum"],
            parameters=[path_param("code", typ="string")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
        "put": op(
            summary="Replace field (retired)",
            tags=["Petroleum"],
            parameters=[path_param("code", typ="string")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
    }
    for path, pk, label in (
        ("/api/v1/oil-gas/fields/{field_id}/report-facts/", "field_id", "Oil field"),
        ("/api/v1/oil-gas/refineries/{refinery_id}/report-facts/", "refinery_id", "Refinery"),
        ("/api/v1/oil-gas/fuel-stations/{facility_id}/report-facts/", "facility_id", "Fuel station"),
        ("/api/v1/oil-gas/wells/{well_id}/report-facts/", "well_id", "Oil well"),
        ("/api/v1/oil-gas/storage-depots/{facility_id}/report-facts/", "facility_id", "Storage depot"),
        ("/api/v1/oil-gas/pipelines/{pipeline_id}/report-facts/", "pipeline_id", "Pipeline"),
    ):
        paths.update(_facts(path, "Petroleum", f"{label} + Info facts", pk))
    paths.update(_gone_post("/api/v1/oil-gas/operations/daily/", "Petroleum", "Daily operations upsert (retired)"))
    paths.update(_gone_post("/api/v1/oil-gas/operations/publish/", "Petroleum", "Daily operations publish (retired)"))
    paths["/api/v1/oil-gas/targets/catalog/"] = {
        "get": op(
            summary="Petroleum target metric catalog",
            tags=["Petroleum"],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        )
    }
    paths["/api/v1/oil-gas/targets/"] = {
        "get": op(
            summary="List operational targets",
            tags=["Petroleum"],
            parameters=[
                q("metric_key"),
                q("scope_type"),
                q("scope_code"),
                q("period_start", format="date"),
            ],
            responses=responses("401", "403", extra=_ok({"type": "array", "items": {"type": "object"}})),
        ),
        "post": op(
            summary="Create target (retired)",
            tags=["Petroleum"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
    }
    paths["/api/v1/oil-gas/targets/compare/"] = {
        "get": op(
            summary="Compare targets vs actuals",
            tags=["Petroleum"],
            parameters=[DATE_Q, q("scope_type"), q("scope_code"), q("metric_key")],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/oil-gas/targets/coverage/"] = {
        "get": op(
            summary="Target coverage",
            tags=["Petroleum"],
            parameters=[DATE_Q],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/oil-gas/targets/fields/"] = {
        "get": op(
            summary="Field target matrix (crude_oil_bbl)",
            tags=["Petroleum"],
            parameters=[DATE_Q],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/oil-gas/targets/monthly/"] = {
        "get": op(
            summary="Monthly target rollup",
            tags=["Petroleum"],
            parameters=[DATE_Q, q("scope_type"), q("scope_code")],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/oil-gas/targets/{pk}/"] = {
        "get": op(
            summary="Retrieve operational target",
            tags=["Petroleum"],
            parameters=[path_param("pk")],
            responses=responses("401", "403", "404", extra=_ok({"type": "object"})),
        ),
        "patch": op(
            summary="Update target (retired)",
            tags=["Petroleum"],
            parameters=[path_param("pk")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
        "put": op(
            summary="Replace target (retired)",
            tags=["Petroleum"],
            parameters=[path_param("pk")],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
        "delete": op(
            summary="Delete target (retired)",
            tags=["Petroleum"],
            parameters=[path_param("pk")],
            responses=responses("401", "403", "410"),
        ),
    }
    paths.update(_admin_crud("/api/v1/oil-gas", "Petroleum"))

    # ── Water ───────────────────────────────────────────────────────────────
    paths["/api/v1/water/sector-info-dashboard/"] = {
        "get": op(
            summary="National water KPI strip",
            tags=["Water"],
            parameters=[q("year", typ="integer")],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/water/rainfall/dashboard/"] = {
        "get": op(
            summary="Rainfall dashboard",
            tags=["Water"],
            parameters=[q("year", typ="integer"), q("basin"), q("governorate")],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/water/dams/dashboard/"] = {
        "get": op(
            summary="Dams dashboard",
            tags=["Water"],
            parameters=[q("year", typ="integer"), q("governorate")],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/water/dams/map-catalog/"] = {
        "get": op(
            summary="Dams map catalog",
            tags=["Water"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/water/dams/euphrates/dashboard/"] = {
        "get": op(
            summary="Euphrates dashboard",
            tags=["Water"],
            parameters=[q("month", description="YYYY-MM")],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/water/drinking-water/dashboard/"] = {
        "get": op(
            summary="Drinking-water dashboard",
            tags=["Water"],
            parameters=DRINKING_FILTERS,
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/water/drinking-water/stations/"] = {
        "get": op(
            summary="Drinking-water stations",
            tags=["Water"],
            parameters=DRINKING_FILTERS
            + [
                q("offset", typ="integer", default=0),
                q("limit", typ="integer", default=50),
            ],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    for path, pk, label in (
        ("/api/v1/water/drinking-water/stations/{station_id}/report-facts/", "station_id", "Drinking station"),
        ("/api/v1/water/dams/{dam_id}/report-facts/", "dam_id", "Dam"),
        ("/api/v1/water/rainfall/stations/{station_id}/report-facts/", "station_id", "Rainfall station"),
        ("/api/v1/water/rainfall/basins/{basin_id}/report-facts/", "basin_id", "Rainfall basin"),
        ("/api/v1/water/springs/{feature_id}/report-facts/", "feature_id", "Spring"),
        ("/api/v1/water/lakes/{feature_id}/report-facts/", "feature_id", "Lake"),
        ("/api/v1/water/rivers/{feature_id}/report-facts/", "feature_id", "River"),
        ("/api/v1/water/streams/{feature_id}/report-facts/", "feature_id", "Stream"),
        ("/api/v1/water/geology-units/{feature_id}/report-facts/", "feature_id", "Geology unit"),
    ):
        paths.update(_facts(path, "Water", f"{label} + Info facts", pk))
    paths["/api/v1/water/reports/export/"] = {
        "get": op(
            summary="Export a water dashboard section",
            tags=["Water"],
            parameters=[
                q(
                    "section",
                    required=True,
                    enum=["rainfall", "dams", "euphrates", "drinking-water"],
                ),
                q("year", typ="integer"),
                q("month", description="YYYY-MM (Euphrates)."),
                q("basin"),
                q("governorate"),
                FORMAT_XLSX_PDF,
            ],
            responses=responses("400", "401", "403", extra=_file()),
        )
    }
    paths["/api/v1/water/admin/imports/status/"] = {
        "get": op(
            summary="Water import status",
            tags=["Water"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    paths["/api/v1/water/admin/lookups/"] = {
        "get": op(
            summary="Water admin lookups",
            tags=["Water"],
            responses=responses("401", "403", extra=_ok({"type": "object"})),
        )
    }
    for import_path in (
        "/api/v1/water/admin/imports/rainfall/",
        "/api/v1/water/admin/imports/rainfall/clear/",
        "/api/v1/water/admin/imports/dams/",
        "/api/v1/water/admin/imports/dams/clear/",
        "/api/v1/water/admin/imports/euphrates/",
        "/api/v1/water/admin/imports/euphrates/clear/",
        "/api/v1/water/admin/imports/drinking-water/geo/",
        "/api/v1/water/admin/imports/drinking-water/survey/",
    ):
        paths.update(_gone_post(import_path, "Water", "Import/clear (retired)"))
    paths["/api/v1/water/admin/exports/drinking-water/survey/"] = {
        "get": op(
            summary="Export drinking-water survey workbook",
            tags=["Water"],
            responses=responses("401", "403", extra=_file("xlsx")),
        )
    }
    for tpl, label in (
        ("rainfall", "rainfall"),
        ("dams-metadata", "dam metadata"),
        ("dams-storage", "dam storage"),
        ("euphrates", "Euphrates"),
        ("drinking-water-survey", "drinking-water survey"),
    ):
        paths[f"/api/v1/water/admin/templates/{tpl}/"] = {
            "get": op(
                summary=f"Download {label} Excel template",
                tags=["Water"],
                responses=responses("401", "403", extra=_file("xlsx")),
            )
        }
    paths["/api/v1/water/admin/daily/euphrates/"] = {
        "get": op(
            summary="Read Euphrates daily reading",
            tags=["Water"],
            parameters=[DATE_Q],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        ),
        "post": op(
            summary="Write Euphrates daily (retired)",
            tags=["Water"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
    }
    paths.update(_gone_post("/api/v1/water/admin/daily/dam-storage/", "Water", "Dam storage daily (retired)"))
    paths.update(_gone_post("/api/v1/water/admin/daily/rainfall/", "Water", "Rainfall daily (retired)"))
    paths["/api/v1/water/admin/daily/drinking-water/"] = {
        "get": op(
            summary="Read drinking-water station snapshot",
            tags=["Water"],
            parameters=[q("station_id", typ="integer", required=True)],
            responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
        ),
        "post": op(
            summary="Write drinking-water daily (retired)",
            tags=["Water"],
            request_body=_json_body({"type": "object"}),
            responses=responses("401", "403", "410"),
        ),
    }
    paths.update(_admin_crud("/api/v1/water", "Water"))

    return paths


def _sector_reports(prefix: str, tag: str) -> dict[str, Any]:
    return {
        f"{prefix}/report-dates/": {
            "get": op(
                summary="Available report dates",
                tags=[tag],
                responses=responses(
                    "401",
                    "403",
                    extra=_ok(
                        {
                            "type": "object",
                            "properties": {
                                "dates": {"type": "array", "items": {"type": "string"}}
                            },
                        }
                    ),
                ),
            )
        },
        f"{prefix}/reports/": {
            "get": op(
                summary="Recent DailyReport rows",
                tags=[tag],
                responses=responses(
                    "401",
                    "403",
                    extra=_ok({"type": "array", "items": {"type": "object"}}),
                ),
            )
        },
        f"{prefix}/reports/detail/": {
            "get": op(
                summary="Full report for a date",
                tags=[tag],
                parameters=[DATE_Q],
                responses=responses("400", "401", "403", "404", extra=_ok({"type": "object"})),
            )
        },
        f"{prefix}/reports/export/": {
            "get": op(
                summary="Download dated sector report",
                tags=[tag],
                parameters=[DATE_Q, FORMAT_XLSX_PDF],
                responses=responses("400", "401", "403", "404", extra=_file()),
            )
        },
        f"{prefix}/reports/template/": {
            "get": op(
                summary="Download import template",
                tags=[tag],
                parameters=[q("date", format="date")],
                responses=responses("401", "403", extra=_file("xlsx")),
            )
        },
        f"{prefix}/reports/import/": {
            "post": op(
                summary="Import Excel report",
                tags=[tag],
                request_body=_multipart(
                    {
                        "file": {"type": "string", "format": "binary"},
                        "publish": {
                            "type": "string",
                            "description": "1/true/yes/on/published (default true).",
                        },
                    },
                    ["file"],
                ),
                responses=responses("400", "401", "403", extra=_ok({"type": "object"})),
            )
        },
        f"{prefix}/reports/upsert/": {
            "post": op(
                summary="Upsert daily report (retired)",
                tags=[tag],
                request_body=_json_body({"type": "object"}),
                responses=responses("401", "403", "410"),
            )
        },
    }
