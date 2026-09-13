"""Dataset serialisation and sector scoping.

Split out of the old Ninja `api.py` so the payload shapes live apart from the
framework that serves them — the views below are thin, and these functions are
what `tests/parity` ultimately protects.

The scope helpers take a user rather than a request: what they decide depends on
the caller's permissions, not on how the caller arrived.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from accounts.permissions import allowed_view_sectors, user_can_view_sector
from config.api_errors import detail_error
from projects.models import ProjectGovernorate, ProjectOrganization, Sector
from rest_framework.exceptions import PermissionDenied

from .models import Dataset, DatasetResource, DatasetStatus
from .services import (
    _effective_resource_formats,
    _format_from_file,
    _normalize_formats,
    parse_resource_formats,
)

_MAX_SOURCE_FILE_BYTES = 50 * 1024 * 1024


def assert_dataset_sector_access(user, dataset: Dataset):
    """Raise unless the caller may see this dataset's sector."""
    if user.is_portal_admin or user.can_manage_datasets:
        return user
    if not user_can_view_sector(user, dataset.sector):
        raise PermissionDenied('Sector permission required.')
    return user


def apply_sector_scope(user, params: dict[str, Any], sector_value: str) -> dict[str, Any]:
    """Restrict dataset list/meta queries to sectors the user may view."""
    if user.is_portal_admin or user.can_manage_datasets:
        if sector_value:
            params['sector'] = sector_value
        return params

    allowed = allowed_view_sectors(user)
    if not allowed:
        raise PermissionDenied('Sector permission required.')

    if sector_value:
        if sector_value not in allowed:
            raise PermissionDenied('Sector permission required.')
        params['sector'] = sector_value
        return params

    if len(allowed) == 1:
        params['sector'] = allowed[0]
    else:
        params['sectors'] = allowed
    return params


def _abs_url(request, url: str | None) -> str | None:
    if not url:
        return None
    return request.build_absolute_uri(url) if request else url


def serialize_organization(organization: ProjectOrganization) -> dict[str, Any]:
    return {
        'id': organization.id,
        'slug': organization.slug,
        'acronym': organization.acronym,
        'name_en': organization.name_en,
    }


def serialize_governorate(governorate: ProjectGovernorate) -> dict[str, Any]:
    data = {
        'id': governorate.id,
        'pcode': governorate.pcode,
        'name_en': governorate.name_en,
        'name_ar': governorate.name_ar,
    }
    if hasattr(governorate, 'dataset_count'):
        data['dataset_count'] = governorate.dataset_count
    return data


def serialize_resource(resource: DatasetResource, request=None) -> dict[str, Any]:
    file_name = resource.file.name.rsplit('/', 1)[-1]
    return {
        'id': resource.id,
        'file_url': _abs_url(request, resource.file.url),
        'file_name': file_name,
        'format': _format_from_file(file_name, resource.file),
        'download_url': (
            request.build_absolute_uri(
                f'/api/v1/datasets/{resource.dataset_id}/download/?resource_id={resource.pk}',
            )
            if request
            else None
        ),
        'sort_order': resource.sort_order,
        'created_at': resource.created_at.isoformat() if resource.created_at else None,
    }


def serialize_dataset(dataset: Dataset, request=None) -> dict[str, Any]:
    resources = list(dataset.resources.all())
    primary = resources[0] if resources else None
    if primary:
        file_url = _abs_url(request, primary.file.url)
        file_name = primary.file.name.rsplit('/', 1)[-1]
    elif dataset.source_file:
        file_url = _abs_url(request, dataset.source_file.url)
        file_name = dataset.source_file.name.rsplit('/', 1)[-1]
    else:
        file_url = None
        file_name = None

    return {
        'id': dataset.id,
        'title_en': dataset.title_en,
        'title_ar': dataset.title_ar,
        'slug': dataset.slug,
        'description_en': dataset.description_en,
        'description_ar': dataset.description_ar,
        'organization': serialize_organization(dataset.organization),
        'governorate': serialize_governorate(dataset.governorate),
        'sector': dataset.sector,
        'sector_display': dataset.sector_display,
        'resource_formats': _effective_resource_formats(dataset),
        'resources': [serialize_resource(row, request) for row in resources],
        'external_url': dataset.external_url,
        'file_url': file_url,
        'file_name': file_name,
        'download_url': (
            request.build_absolute_uri(f'/api/v1/datasets/{dataset.pk}/download/')
            if request and dataset.has_download
            else None
        ),
        'has_download': dataset.has_download,
        'data_start_date': dataset.data_start_date.isoformat() if dataset.data_start_date else None,
        'data_end_date': dataset.data_end_date.isoformat() if dataset.data_end_date else None,
        'download_count': dataset.download_count,
        'view_count': dataset.view_count,
        'status': dataset.status,
        'status_display': dataset.status_display,
        'is_active': dataset.is_active,
        'created_at': dataset.created_at.isoformat() if dataset.created_at else None,
        'updated_at': dataset.updated_at.isoformat() if dataset.updated_at else None,
    }


def _parse_json_body(request) -> dict[str, Any]:
    if not request.body:
        return {}
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        raise detail_error( 'Invalid JSON.')
    if not isinstance(data, dict):
        raise detail_error( 'Expected a JSON object.')
    return data


def _raw_write_payload(request):
    content_type = (getattr(request, 'content_type', None) or '').lower()
    if 'application/json' in content_type:
        return _parse_json_body(request)
    return request.POST


def _wants_clear_source_file(data) -> bool:
    if hasattr(data, 'get'):
        value = data.get('clear_source_file')
    else:
        value = None
    return value in (True, 'true', 'True', '1', 1)


def _parse_optional_date(value: Any) -> date | None:
    if value in (None, ''):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise detail_error( 'Invalid date.')


def _parse_bool(value: Any, default: bool | None = None) -> bool | None:
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ('true', '1', 'yes'):
            return True
        if lowered in ('false', '0', 'no'):
            return False
    return bool(value)


def _parse_non_negative_int(value: Any, *, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise detail_error( f'Invalid value for {field}.')
    return max(parsed, 0)


def _validate_dataset_write(
    data: dict[str, Any],
    *,
    partial: bool = False,
    instance: Dataset | None = None,
) -> dict[str, Any]:
    allowed = {
        'title_en',
        'title_ar',
        'description_en',
        'description_ar',
        'organization_id',
        'governorate_id',
        'sector',
        'resource_formats',
        'source_file',
        'external_url',
        'data_start_date',
        'data_end_date',
        'download_count',
        'view_count',
        'status',
        'is_active',
    }
    payload: dict[str, Any] = {key: value for key, value in data.items() if key in allowed}

    if not partial:
        required = ('title_en', 'organization_id', 'governorate_id', 'sector')
        missing = [field for field in required if field not in payload or payload[field] in (None, '')]
        if missing:
            raise detail_error( f'Missing required fields: {", ".join(missing)}.')

    if 'organization_id' in payload:
        try:
            organization = ProjectOrganization.objects.get(pk=int(payload.pop('organization_id')))
        except (TypeError, ValueError, ProjectOrganization.DoesNotExist):
            raise detail_error( 'Invalid organization_id.')
        payload['organization'] = organization

    if 'governorate_id' in payload:
        try:
            governorate = ProjectGovernorate.objects.get(pk=int(payload.pop('governorate_id')))
        except (TypeError, ValueError, ProjectGovernorate.DoesNotExist):
            raise detail_error( 'Invalid governorate_id.')
        payload['governorate'] = governorate

    if 'sector' in payload and payload['sector'] not in Sector.values:
        raise detail_error( 'Invalid sector.')

    if 'status' in payload and payload['status'] not in DatasetStatus.values:
        raise detail_error( 'Invalid status.')

    if 'resource_formats' in payload:
        parsed = parse_resource_formats(payload['resource_formats'])
        normalized = _normalize_formats(parsed)
        if parsed and not normalized:
            raise detail_error( 'One or more selected formats are invalid.')
        payload['resource_formats'] = normalized

    if 'source_file' in payload:
        source_file = payload['source_file']
        if source_file in (None, '', False):
            payload.pop('source_file')
        elif hasattr(source_file, 'size') and source_file.size > _MAX_SOURCE_FILE_BYTES:
            raise detail_error( 'File must be 50 MB or smaller.')

    if 'data_start_date' in payload:
        payload['data_start_date'] = _parse_optional_date(payload['data_start_date'])

    if 'data_end_date' in payload:
        payload['data_end_date'] = _parse_optional_date(payload['data_end_date'])

    if 'download_count' in payload:
        payload['download_count'] = _parse_non_negative_int(payload['download_count'], field='download_count')

    if 'view_count' in payload:
        payload['view_count'] = _parse_non_negative_int(payload['view_count'], field='view_count')

    if 'is_active' in payload:
        parsed = _parse_bool(payload['is_active'])
        if parsed is None:
            payload.pop('is_active')
        else:
            payload['is_active'] = parsed

    start = payload.get('data_start_date')
    end = payload.get('data_end_date')
    if partial and instance:
        if 'data_start_date' not in payload:
            start = instance.data_start_date
        if 'data_end_date' not in payload:
            end = instance.data_end_date
    if start and end and end < start:
        raise detail_error( 'End date must be on or after start date.')

    return payload


def _parse_resource_id(raw: str | None) -> int | None:
    if raw and raw.isdigit():
        return int(raw)
    return None
