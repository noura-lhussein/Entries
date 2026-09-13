"""Dataset catalogue endpoints.

Converted from Django Ninja; URLs, payloads and status codes are unchanged and
guarded by `tests/parity`. Serialisation and sector scoping live in `serialize.py`
so these views stay thin.

Writes (create / update / delete) answer 410: datasets are edited through
report_moe's master-data screens, which are now part of this same backend.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from django.db import transaction
from django.http import FileResponse
from projects.models import Sector
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Dataset, DatasetStatus
from .serialize import (
    _parse_resource_id,
    apply_sector_scope,
    assert_dataset_sector_access,
    serialize_dataset,
    serialize_governorate,
    serialize_organization,
)
from .services import (
    build_datasets_meta,
    get_dataset,
    get_dataset_resource,
    list_datasets,
    record_dataset_download,
    record_dataset_view,
)
from .spatial_conversion import (
    build_dataset_spatial_slices,
    build_spatial_slices_from_path,
    is_shapefile_file,
    is_shapefile_spatial_dataset,
)


class Gone(APIException):
    """410, so callers see that the route moved rather than a generic failure."""

    status_code = 410


def _active_or_404(dataset: Dataset) -> None:
    if not dataset.is_active or dataset.status != DatasetStatus.ACTIVE:
        raise NotFound("Not available.")


def _load(pk: int, user) -> Dataset:
    try:
        dataset = get_dataset(pk)
    except Dataset.DoesNotExist:
        raise NotFound("Not found.")
    assert_dataset_sector_access(user, dataset)
    return dataset


def _file_response(file_field, *, attachment: bool):
    filename = file_field.name.rsplit("/", 1)[-1]
    response = FileResponse(
        file_field.open("rb"), as_attachment=attachment, filename=filename
    )
    if not attachment:
        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            response["Content-Type"] = content_type
        response["Content-Disposition"] = 'inline; filename="' + filename + '"'
    try:
        response["Content-Length"] = file_field.size
    except Exception:  # noqa: BLE001 — a missing size must not fail the download
        pass
    return response


def _slices(builder, arg):
    try:
        return builder(arg)
    except ValueError as exc:
        raise ValidationError(str(exc))
    except Exception:  # noqa: BLE001 — shapefile parsing fails in many ways
        raise APIException("Could not convert shapefile to GeoJSON.")


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def dataset_list(request):
    if request.method == "POST":
        raise Gone(
            "Dataset create moved to report_moe master-data. Use report_moe UI/API."
        )

    include = request.query_params.get("include_inactive") == "1"
    params = {
        "search": request.query_params.get("search", ""),
        "format": request.query_params.get("format", ""),
        "organization": request.query_params.get("organization", ""),
        "sector": request.query_params.get("sector", ""),
        "governorate": request.query_params.get("governorate", ""),
        "status": request.query_params.get(
            "status", "all" if include else DatasetStatus.ACTIVE
        ),
        "ordering": request.query_params.get("ordering", "-updated_at"),
        "page": request.query_params.get("page", "1"),
        "page_size": request.query_params.get("page_size", "10"),
    }
    sector_value = (params.get("sector") or "").strip()
    if sector_value and sector_value not in Sector.values:
        raise ValidationError("Invalid sector.")

    params = apply_sector_scope(request.user, params, sector_value)
    payload = list_datasets(params, include_inactive=include)
    return Response(
        {
            "count": payload["count"],
            "page": payload["page"],
            "page_size": payload["page_size"],
            "results": [serialize_dataset(row, request) for row in payload["results"]],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def datasets_meta(request):
    sector_value = (request.query_params.get("sector") or "").strip()
    if sector_value and sector_value not in Sector.values:
        raise ValidationError("Invalid sector.")
    scoped = apply_sector_scope(request.user, {}, sector_value)
    payload = build_datasets_meta(
        sector=scoped.get("sector") or None,
        sectors=scoped.get("sectors"),
        status=(request.query_params.get("status")
                or DatasetStatus.ACTIVE).strip(),
        governorate=(request.query_params.get(
            "governorate") or "").strip() or None,
        format=(request.query_params.get("format") or "").strip() or None,
    )
    return Response(
        {
            "active_count": payload["active_count"],
            "archived_count": payload["archived_count"],
            "sectors": payload["sectors"],
            "statuses": payload["statuses"],
            "format_options": payload["format_options"],
            "formats": payload["formats"],
            "governorates": [serialize_governorate(r) for r in payload["governorates"]],
            "organizations": [
                serialize_organization(r) for r in payload["organizations"]
            ],
        }
    )


# ATOMIC_REQUESTS would commit before the file is streamed, so the request would
# hold a transaction open for the whole download without protecting anything.
@transaction.non_atomic_requests
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_dataset(request, pk: int):
    dataset = _load(pk, request.user)
    _active_or_404(dataset)
    resource = get_dataset_resource(
        dataset, _parse_resource_id(request.query_params.get("resource_id"))
    )
    if resource:
        record_dataset_download(dataset)
        return _file_response(resource.file, attachment=True)
    if dataset.source_file:
        record_dataset_download(dataset)
        return _file_response(dataset.source_file, attachment=True)
    if dataset.external_url:
        raise ValidationError("Use external_url for this dataset.")
    raise NotFound("No download available for this dataset.")


@transaction.non_atomic_requests
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def preview_dataset(request, pk: int):
    dataset = _load(pk, request.user)
    _active_or_404(dataset)
    resource = get_dataset_resource(
        dataset, _parse_resource_id(request.query_params.get("resource_id"))
    )
    preview_file = resource.file if resource else dataset.source_file
    if not preview_file:
        raise NotFound("No file to preview.")
    return _file_response(preview_file, attachment=False)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dataset_spatial_layers(request, pk: int):
    dataset = _load(pk, request.user)
    _active_or_404(dataset)
    resource = get_dataset_resource(
        dataset, _parse_resource_id(request.query_params.get("resource_id"))
    )

    if resource:
        path = Path(resource.file.path)
        if not is_shapefile_file(path, resource.file.name.rsplit("/", 1)[-1]):
            raise ValidationError("This file is not a shapefile archive.")
        slices = _slices(build_spatial_slices_from_path, path)
    else:
        if not dataset.source_file:
            raise NotFound("No spatial file available.")
        if not is_shapefile_spatial_dataset(dataset):
            raise ValidationError("This dataset is not a shapefile archive.")
        slices = _slices(build_dataset_spatial_slices, dataset)

    if not slices:
        raise NotFound("No features found in shapefile.")
    return Response({"slices": slices})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def record_download(request, pk: int):
    dataset = _load(pk, request.user)
    if (
        not dataset.is_active
        or dataset.status != DatasetStatus.ACTIVE
        or not dataset.has_download
    ):
        raise NotFound("Not available.")
    record_dataset_download(dataset)
    return Response({"download_count": dataset.download_count})


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def dataset_detail(request, pk: int):
    if request.method == "PATCH":
        raise Gone(
            "Dataset update moved to report_moe master-data. Use report_moe UI/API."
        )
    if request.method == "DELETE":
        raise Gone(
            "Dataset delete moved to report_moe master-data. Use report_moe UI/API."
        )

    dataset = _load(pk, request.user)
    if request.query_params.get("track_view") == "1":
        record_dataset_view(dataset)
    return Response(serialize_dataset(dataset, request))
