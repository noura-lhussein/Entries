"""OpenAPI 3.0 schema for the unified MOE API.

ViewSet request/response bodies are derived from DRF serializers so they stay
aligned with the code. Function views are documented in `openapi_catalog`.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers


def _field_schema(field: serializers.Field) -> dict[str, Any]:
    if getattr(field, "many", False) and hasattr(field, "child"):
        return {"type": "array", "items": _field_schema(field.child)}

    if isinstance(field, serializers.ListField):
        child = getattr(field, "child", None)
        items = _field_schema(child) if child is not None else {"type": "string"}
        return {"type": "array", "items": items}

    if isinstance(field, serializers.Serializer):
        return serializer_schema(field.__class__)

    if isinstance(field, (serializers.IntegerField, serializers.PrimaryKeyRelatedField)):
        schema: dict[str, Any] = {"type": "integer"}
    elif isinstance(field, serializers.BooleanField):
        schema = {"type": "boolean"}
    elif isinstance(field, serializers.FloatField):
        schema = {"type": "number"}
    elif isinstance(field, serializers.DecimalField):
        schema = {"type": "string", "format": "decimal"}
    elif isinstance(field, serializers.DateField):
        schema = {"type": "string", "format": "date"}
    elif isinstance(field, serializers.DateTimeField):
        schema = {"type": "string", "format": "date-time"}
    elif isinstance(field, serializers.EmailField):
        schema = {"type": "string", "format": "email"}
    elif isinstance(field, serializers.URLField):
        schema = {"type": "string", "format": "uri"}
    elif isinstance(field, serializers.JSONField):
        schema = {"type": "object", "additionalProperties": True}
    elif isinstance(field, serializers.FileField):
        schema = {"type": "string", "format": "binary"}
    elif isinstance(field, serializers.ChoiceField):
        schema = {"type": "string", "enum": [str(c) for c in field.choices]}
    else:
        schema = {"type": "string"}

    if getattr(field, "allow_null", False):
        schema["nullable"] = True
    help_text = getattr(field, "help_text", None)
    if help_text:
        schema["description"] = str(help_text)
    return schema


def serializer_schema(serializer_class) -> dict[str, Any]:
    instance = serializer_class()
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, field in instance.fields.items():
        properties[name] = _field_schema(field)
        if field.required and not field.read_only:
            required.append(name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def paginated(item_ref: str) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "count": {"type": "integer"},
            "next": {"type": "string", "nullable": True},
            "previous": {"type": "string", "nullable": True},
            "results": {
                "type": "array",
                "items": {"$ref": f"#/components/schemas/{item_ref}"},
            },
        },
    }


def _ref(name: str) -> dict[str, Any]:
    return {"$ref": f"#/components/schemas/{name}"}


def _json(schema: dict[str, Any]) -> dict[str, Any]:
    return {"application/json": {"schema": schema}}


def _q(
    name: str,
    *,
    typ: str = "string",
    required: bool = False,
    description: str = "",
    enum: list[str] | None = None,
    example: Any = None,
    default: Any = None,
    format: str | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": typ}
    if enum:
        schema["enum"] = enum
    if example is not None:
        schema["example"] = example
    if default is not None:
        schema["default"] = default
    if format:
        schema["format"] = format
    param: dict[str, Any] = {
        "name": name,
        "in": "query",
        "required": required,
        "schema": schema,
    }
    if description:
        param["description"] = description
    return param


def _path(name: str, *, typ: str = "integer", description: str = "") -> dict[str, Any]:
    param: dict[str, Any] = {
        "name": name,
        "in": "path",
        "required": True,
        "schema": {"type": typ},
    }
    if description:
        param["description"] = description
    return param


PAGE_PARAMS = [
    _q("page", typ="integer", description="Page number (1-based).", default=1),
    _q("page_size", typ="integer", description="Results per page.", default=20),
    _q("search", description="Search string (when the viewset defines search_fields)."),
    _q("ordering", description="Order by field. Prefix with `-` for descending."),
]

ERROR = {
    "Error": {
        "type": "object",
        "properties": {"detail": {"type": "string"}},
        "required": ["detail"],
    },
    "Gone": {
        "type": "object",
        "properties": {"detail": {"type": "string"}},
        "description": "410 — write/import moved to report_moe Form Builder / Info.",
    },
}

COMMON_ERRORS = {
    "400": {"description": "Bad request", "content": _json(_ref("Error"))},
    "401": {"description": "Not authenticated", "content": _json(_ref("Error"))},
    "403": {"description": "Permission denied", "content": _json(_ref("Error"))},
    "404": {"description": "Not found", "content": _json(_ref("Error"))},
    "409": {"description": "Conflict", "content": _json(_ref("Error"))},
    "410": {"description": "Gone — use report_moe Form Builder / Info", "content": _json(_ref("Gone"))},
    "429": {"description": "Too many requests", "content": _json(_ref("Error"))},
}


def _responses(*codes: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    out = {c: COMMON_ERRORS[c] for c in codes if c in COMMON_ERRORS}
    if extra:
        out.update(extra)
    return out


def _op(
    *,
    summary: str,
    tags: list[str],
    description: str = "",
    parameters: list[dict[str, Any]] | None = None,
    request_body: dict[str, Any] | None = None,
    responses: dict[str, Any] | None = None,
    security: list[dict[str, list]] | None = None,
) -> dict[str, Any]:
    op: dict[str, Any] = {"summary": summary, "tags": tags}
    if description:
        op["description"] = description
    if parameters:
        op["parameters"] = parameters
    if request_body:
        op["requestBody"] = request_body
    op["responses"] = responses or _responses("401", "403")
    if security is not None:
        op["security"] = security
    return op


def _merge_path(paths: dict[str, Any], path: str, methods: dict[str, Any]) -> None:
    bucket = paths.setdefault(path, {})
    bucket.update(methods)


def _serializer_components() -> dict[str, Any]:
    from dynamic_forms.serializers import (
        AttributeSerializer,
        InfoSerializer,
        MainSectionSerializer,
        OptionSerializer,
        ReqReportSerializer,
        SubMainSectionSerializer,
        TitleCategorySerializer,
        TitleSerializer,
        UserCreateSerializer,
        UserSerializer,
        UserSubMainSerializer,
        UserTitleCategorySerializer,
        UserTitleSerializer,
        UserUpdateSerializer,
    )
    from dynamic_forms.serializers.info_serializers import InfoRowDataSerializer
    from locations.serializers import (
        CommunitySerializer,
        DistrictSerializer,
        GovernorateSerializer,
        SubDistrictSerializer,
    )
    from project_budget.serializers import (
        AnnualBudgetSerializer,
        CurrencySerializer,
        FoundationSerializer,
        MeasureUnitSerializer,
        MilestoneSerializer,
        MilestoneTransactionSerializer,
        PolicySerializer,
        ProjectCategorySerializer,
        ProjectChangeLogSerializer,
        ProjectSerializer,
        ProjectTransactionSerializer,
        ProjectTypeSerializer,
        ResponsibleSerializer,
        TargetSerializer,
        TransactionSerializer,
    )
    from project_budget.serializers.budget_user_serializers import (
        BudgetUserCreateSerializer,
        BudgetUserSerializer,
        BudgetUserUpdateSerializer,
    )

    mapping = {
        "User": UserSerializer,
        "UserCreate": UserCreateSerializer,
        "UserUpdate": UserUpdateSerializer,
        "MainSection": MainSectionSerializer,
        "SubMainSection": SubMainSectionSerializer,
        "TitleCategory": TitleCategorySerializer,
        "Title": TitleSerializer,
        "Attribute": AttributeSerializer,
        "Option": OptionSerializer,
        "ReqReport": ReqReportSerializer,
        "Info": InfoSerializer,
        "InfoRow": InfoRowDataSerializer,
        "UserSubMain": UserSubMainSerializer,
        "UserTitle": UserTitleSerializer,
        "UserTitleCategory": UserTitleCategorySerializer,
        "Governorate": GovernorateSerializer,
        "District": DistrictSerializer,
        "SubDistrict": SubDistrictSerializer,
        "Community": CommunitySerializer,
        "BudgetCategory": ProjectCategorySerializer,
        "Foundation": FoundationSerializer,
        "Responsible": ResponsibleSerializer,
        "ProjectType": ProjectTypeSerializer,
        "Currency": CurrencySerializer,
        "BudgetProject": ProjectSerializer,
        "ProjectChangeLog": ProjectChangeLogSerializer,
        "Milestone": MilestoneSerializer,
        "Target": TargetSerializer,
        "Policy": PolicySerializer,
        "MeasureUnit": MeasureUnitSerializer,
        "AnnualBudget": AnnualBudgetSerializer,
        "ProjectTransaction": ProjectTransactionSerializer,
        "MilestoneTransaction": MilestoneTransactionSerializer,
        "Transaction": TransactionSerializer,
        "BudgetUser": BudgetUserSerializer,
        "BudgetUserCreate": BudgetUserCreateSerializer,
        "BudgetUserUpdate": BudgetUserUpdateSerializer,
    }
    return {name: serializer_schema(cls) for name, cls in mapping.items()}


def _crud_paths() -> dict[str, Any]:
    """Standard list/create + retrieve/update/destroy for DRF ViewSets."""
    resources = [
        {
            "path": "/api/v1/users",
            "pk": "id",
            "tag": "Users",
            "schema": "User",
            "create": "UserCreate",
            "update": "UserUpdate",
            "list_params": PAGE_PARAMS + [
                _q("is_active", typ="boolean"),
                _q("status"),
                _q("parent"),
            ],
            "search": "email, full_name",
        },
        {
            "path": "/api/v1/main-sections",
            "pk": "id",
            "tag": "Form builder",
            "schema": "MainSection",
        },
        {
            "path": "/api/v1/sub-sections",
            "pk": "id",
            "tag": "Form builder",
            "schema": "SubMainSection",
            "list_params": PAGE_PARAMS + [
                _q("main_section", typ="integer", description="Filter by main section id."),
                _q("parent", typ="integer", description="Filter by parent sub-section id."),
                _q("leaves", description="If truthy, return only leaf sections."),
            ],
        },
        {
            "path": "/api/v1/title-categories",
            "pk": "id",
            "tag": "Form builder",
            "schema": "TitleCategory",
        },
        {
            "path": "/api/v1/titles",
            "pk": "id",
            "tag": "Form builder",
            "schema": "Title",
            "list_params": PAGE_PARAMS + [
                _q("category", typ="integer", description="Title category id."),
            ],
        },
        {
            "path": "/api/v1/attributes",
            "pk": "id",
            "tag": "Form builder",
            "schema": "Attribute",
            "list_params": PAGE_PARAMS + [
                _q("title", typ="integer", description="Title id."),
            ],
        },
        {
            "path": "/api/v1/options",
            "pk": "id",
            "tag": "Form builder",
            "schema": "Option",
            "list_params": PAGE_PARAMS + [
                _q("attribute", typ="integer", description="Attribute id."),
            ],
        },
        {
            "path": "/api/v1/reports",
            "pk": "id",
            "tag": "Reports",
            "schema": "ReqReport",
            "read_only": True,
        },
        {
            "path": "/api/v1/infos",
            "pk": "id",
            "tag": "Info",
            "schema": "Info",
            "list_params": PAGE_PARAMS + info_filter_params(),
        },
        {
            "path": "/api/v1/user-sub-mains",
            "pk": "id",
            "tag": "Users",
            "schema": "UserSubMain",
            "list_params": PAGE_PARAMS + [
                _q("user", typ="integer"),
                _q("sub_main", typ="integer"),
            ],
        },
        {
            "path": "/api/v1/user-titles",
            "pk": "id",
            "tag": "Users",
            "schema": "UserTitle",
            "list_params": PAGE_PARAMS + [
                _q("user", typ="integer"),
                _q("title", typ="integer"),
            ],
        },
        {
            "path": "/api/v1/user-title-categories",
            "pk": "id",
            "tag": "Users",
            "schema": "UserTitleCategory",
            "list_params": PAGE_PARAMS + [
                _q("user", typ="integer"),
                _q("category", typ="integer"),
            ],
        },
        {
            "path": "/api/v1/locations/governorates",
            "pk": "id",
            "tag": "Locations",
            "schema": "Governorate",
        },
        {
            "path": "/api/v1/locations/districts",
            "pk": "id",
            "tag": "Locations",
            "schema": "District",
        },
        {
            "path": "/api/v1/locations/subdistricts",
            "pk": "id",
            "tag": "Locations",
            "schema": "SubDistrict",
        },
        {
            "path": "/api/v1/locations/communities",
            "pk": "id",
            "tag": "Locations",
            "schema": "Community",
        },
        {
            "path": "/api/v1/budget/categories",
            "pk": "id",
            "tag": "Budget",
            "schema": "BudgetCategory",
            "options": True,
        },
        {
            "path": "/api/v1/budget/foundations",
            "pk": "id",
            "tag": "Budget",
            "schema": "Foundation",
            "options": True,
        },
        {
            "path": "/api/v1/budget/responsibles",
            "pk": "id",
            "tag": "Budget",
            "schema": "Responsible",
        },
        {
            "path": "/api/v1/budget/project-types",
            "pk": "id",
            "tag": "Budget",
            "schema": "ProjectType",
            "options": True,
        },
        {
            "path": "/api/v1/budget/currencies",
            "pk": "id",
            "tag": "Budget",
            "schema": "Currency",
            "options": True,
        },
        {
            "path": "/api/v1/budget/projects",
            "pk": "id",
            "tag": "Budget",
            "schema": "BudgetProject",
            "list_params": PAGE_PARAMS + [
                _q("status"),
                _q("year", typ="integer", description="Filter by annual_budget year."),
            ],
        },
        {
            "path": "/api/v1/budget/project-change-logs",
            "pk": "id",
            "tag": "Budget",
            "schema": "ProjectChangeLog",
            "read_only": True,
        },
        {
            "path": "/api/v1/budget/milestones",
            "pk": "id",
            "tag": "Budget",
            "schema": "Milestone",
        },
        {
            "path": "/api/v1/budget/targets",
            "pk": "id",
            "tag": "Budget",
            "schema": "Target",
            "options": True,
        },
        {
            "path": "/api/v1/budget/policies",
            "pk": "id",
            "tag": "Budget",
            "schema": "Policy",
            "options": True,
        },
        {
            "path": "/api/v1/budget/measure-units",
            "pk": "id",
            "tag": "Budget",
            "schema": "MeasureUnit",
            "options": True,
        },
        {
            "path": "/api/v1/budget/annual-budgets",
            "pk": "id",
            "tag": "Budget",
            "schema": "AnnualBudget",
            "options": True,
        },
        {
            "path": "/api/v1/budget/project-transactions",
            "pk": "id",
            "tag": "Budget",
            "schema": "ProjectTransaction",
        },
        {
            "path": "/api/v1/budget/milestone-transactions",
            "pk": "id",
            "tag": "Budget",
            "schema": "MilestoneTransaction",
        },
        {
            "path": "/api/v1/budget/transactions",
            "pk": "id",
            "tag": "Budget",
            "schema": "Transaction",
        },
        {
            "path": "/api/v1/budget/users",
            "pk": "id",
            "tag": "Budget",
            "schema": "BudgetUser",
            "create": "BudgetUserCreate",
            "update": "BudgetUserUpdate",
        },
    ]

    paths: dict[str, Any] = {}
    for spec in resources:
        schema = spec["schema"]
        create = spec.get("create", schema)
        update = spec.get("update", schema)
        tag = spec["tag"]
        list_params = spec.get("list_params", PAGE_PARAMS)
        read_only = spec.get("read_only", False)
        collection: dict[str, Any] = {
            "get": _op(
                summary=f"List {schema}",
                tags=[tag],
                parameters=list_params,
                responses=_responses(
                    "401",
                    "403",
                    extra={
                        "200": {
                            "description": "Paginated list",
                            "content": _json(paginated(schema)),
                        }
                    },
                ),
            ),
        }
        if not read_only:
            collection["post"] = _op(
                summary=f"Create {schema}",
                tags=[tag],
                request_body={
                    "required": True,
                    "content": _json(_ref(create)),
                },
                responses=_responses(
                    "400",
                    "401",
                    "403",
                    extra={
                        "201": {
                            "description": "Created",
                            "content": _json(_ref(schema)),
                        }
                    },
                ),
            )
        _merge_path(paths, spec["path"] + "/", collection)

        detail: dict[str, Any] = {
            "get": _op(
                summary=f"Retrieve {schema}",
                tags=[tag],
                parameters=[_path(spec["pk"])],
                responses=_responses(
                    "401",
                    "403",
                    "404",
                    extra={"200": {"description": "OK", "content": _json(_ref(schema))}},
                ),
            ),
        }
        if not read_only:
            detail["put"] = _op(
                summary=f"Replace {schema}",
                tags=[tag],
                parameters=[_path(spec["pk"])],
                request_body={"required": True, "content": _json(_ref(update))},
                responses=_responses(
                    "400",
                    "401",
                    "403",
                    "404",
                    extra={"200": {"description": "OK", "content": _json(_ref(schema))}},
                ),
            )
            detail["patch"] = _op(
                summary=f"Partial update {schema}",
                tags=[tag],
                parameters=[_path(spec["pk"])],
                request_body={"required": True, "content": _json(_ref(update))},
                responses=_responses(
                    "400",
                    "401",
                    "403",
                    "404",
                    extra={"200": {"description": "OK", "content": _json(_ref(schema))}},
                ),
            )
            detail["delete"] = _op(
                summary=f"Delete {schema}",
                tags=[tag],
                parameters=[_path(spec["pk"])],
                responses=_responses(
                    "401",
                    "403",
                    "404",
                    extra={"204": {"description": "Deleted"}},
                ),
            )
        _merge_path(paths, spec["path"] + "/{" + spec["pk"] + "}/", detail)

        if spec.get("options"):
            _merge_path(
                paths,
                spec["path"] + "/options/",
                {
                    "get": _op(
                        summary=f"{schema} dropdown options",
                        tags=[tag],
                        parameters=[
                            _q("exclude", typ="integer", description="Exclude this id."),
                        ],
                        responses=_responses(
                            "400",
                            "401",
                            "403",
                            extra={
                                "200": {
                                    "description": "Lightweight option rows",
                                    "content": _json(
                                        {
                                            "type": "array",
                                            "items": {"type": "object"},
                                        }
                                    ),
                                }
                            },
                        ),
                    )
                },
            )
    return paths


def info_filter_params() -> list[dict[str, Any]]:
    return [
        _q("title_id", description="One or more title ids."),
        _q("title_category_id", description="One or more title category ids."),
        _q("attribute_id"),
        _q("main_section_id"),
        _q("sub_main_id"),
        _q("user", description="Submitter user id."),
        _q("district_id"),
        _q("city_id", description="Governorate id (legacy name)."),
        _q("governorate_id"),
        _q("community_id"),
        _q("confirmed", description="accept / reject / waiting, or true/false."),
        _q("from", format="date", description="Created-at from (YYYY-MM-DD)."),
        _q("to", format="date", description="Created-at to (YYYY-MM-DD)."),
        _q("include_archived", description="Include archived Info rows."),
    ]


def build_openapi(request=None) -> dict[str, Any]:
    from .openapi_catalog import custom_paths, tags

    if request is not None:
        server_url = request.build_absolute_uri("/").rstrip("/")
    else:
        server_url = "http://localhost:8001"

    schemas = {**ERROR, **_serializer_components()}
    schemas.update(
        {
            "LoginRequest": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email or legacy username."},
                    "username": {"type": "string", "description": "Alias for email."},
                    "password": {"type": "string"},
                    "remember": {
                        "type": "boolean",
                        "default": True,
                        "description": "If false, session expires when the browser closes.",
                    },
                },
                "required": ["password"],
                "example": {"email": "admin@example.com", "password": "secret", "remember": True},
            },
            "CsrfToken": {
                "type": "object",
                "properties": {"csrfToken": {"type": "string"}},
                "required": ["csrfToken"],
            },
            "SubmitReportRequest": {
                "type": "object",
                "required": ["sub_main_id", "attribute_values"],
                "properties": {
                    "sub_main_id": {"type": "integer"},
                    "title_id": {"type": "integer", "nullable": True},
                    "attribute_values": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id"],
                            "properties": {
                                "id": {"type": "integer", "description": "Attribute id."},
                                "value": {"description": "Scalar or file URL stored on Info.value."},
                            },
                        },
                    },
                },
            },
            "SubmitFullReportRequest": {
                "type": "object",
                "required": ["sub_main_id", "reports"],
                "properties": {
                    "sub_main_id": {"type": "integer"},
                    "reports": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title_id": {"type": "integer"},
                                "attribute_values": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "value": {},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "SubmitReportResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "created": {"type": "integer"},
                    "skipped": {"type": "integer"},
                },
            },
            "GeoJSONFeatureCollection": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "example": "FeatureCollection"},
                    "features": {"type": "array", "items": {"type": "object"}},
                },
            },
            "AdminRegistry": {
                "type": "object",
                "properties": {
                    "resources": {"type": "array", "items": {"type": "object"}},
                    "groups": {"type": "array", "items": {"type": "object"}},
                },
            },
            "AdminOptions": {
                "type": "object",
                "properties": {
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "value": {},
                                "label": {"type": "string"},
                            },
                        },
                    }
                },
            },
            "AdminList": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "count": {"type": "integer"},
                    "total_count": {"type": "integer"},
                    "page": {"type": "integer"},
                    "page_size": {"type": "integer"},
                    "results": {"type": "array", "items": {"type": "object"}},
                },
            },
            "EntityFacts": {
                "type": "object",
                "description": "Entity record plus accepted Info facts for that entity.",
                "additionalProperties": True,
            },
            "FileUploadResult": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "path": {"type": "string"},
                    "kind": {"type": "string", "enum": ["image", "file"]},
                },
            },
        }
    )

    paths: dict[str, Any] = {}
    paths.update(_crud_paths())
    paths.update(custom_paths())

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "MOE unified API",
            "version": "1.0.0",
            "description": (
                "Django REST Framework API for the portal (`moe-portal`) and "
                "report/budget UI (`front_report_moe`).\n\n"
                "**Auth:** session cookie (`sessionid`) + CSRF. "
                "Call `GET /api/v1/auth/csrf/` then `POST /api/v1/auth/login/`. "
                "Unsafe methods must send `X-CSRFToken` (value of the `csrftoken` cookie). "
                "Anonymous callers receive **401**.\n\n"
                "**Pagination:** `{count, next, previous, results}` unless noted.\n\n"
                "**Export `format`:** sector downloads use `?format=xlsx|pdf` as a file-type "
                "switch (`URL_FORMAT_OVERRIDE` is disabled).\n\n"
                "**410 Gone:** daily operational writes moved to Form Builder / Info."
            ),
        },
        "servers": [{"url": server_url, "description": "Current host"}],
        "tags": tags(),
        "paths": paths,
        "components": {
            "securitySchemes": {
                "cookieAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "sessionid",
                    "description": "Django session cookie set by POST /api/v1/auth/login/.",
                },
                "csrfHeader": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-CSRFToken",
                    "description": "Required on POST/PUT/PATCH/DELETE. Copy from the csrftoken cookie.",
                },
            },
            "schemas": schemas,
        },
        "security": [{"cookieAuth": []}, {"csrfHeader": []}],
    }


# Re-export helpers used by the catalog.
q = _q
path_param = _path
op = _op
responses = _responses
json_content = _json
ref = _ref
merge_path = _merge_path
