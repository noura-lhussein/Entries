from __future__ import annotations

from pathlib import Path
from typing import Any

from django.db.models import Count, Q, QuerySet
from django.utils import timezone
from django.utils.text import slugify
from projects.models import ProjectGovernorate, ProjectOrganization, Sector

from .models import DATASET_FORMAT_CHOICES, Dataset, DatasetResource, DatasetStatus
from .spatial_conversion import infer_zip_archive_format

SECTOR_LABELS_AR = {
    Sector.OIL_GAS: 'البترول',
    Sector.WATER: 'المياه',
    Sector.ELECTRICITY: 'الكهرباء',
    Sector.MINERAL: 'الموارد المعدنية',
    Sector.MULTI: 'متعدد القطاعات',
}

DATASET_STATUS_LABELS_AR = {
    DatasetStatus.ACTIVE: 'نشط',
    DatasetStatus.ARCHIVED: 'مؤرشف',
}

MAX_RESOURCE_FILE_BYTES = 50 * 1024 * 1024

_FORMAT_LOOKUP = {value.upper(): value for value in DATASET_FORMAT_CHOICES}
_EXTENSION_FORMAT_MAP = {
    'csv': 'CSV',
    'xlsx': 'XLSX',
    'xls': 'XLSX',
    'geojson': 'GeoJSON',
    'shp': 'SHP',
    'json': 'JSON',
    'kml': 'KML',
    'kmz': 'KMZ',
    'zip': 'ZIP',
    'pdf': 'PDF',
    'docx': 'DOCX',
}
_FORMAT_FILE_SUFFIXES = {
    'CSV': ('.csv',),
    'XLSX': ('.xlsx', '.xls'),
    'GeoJSON': ('.geojson',),
    'SHP': ('.shp',),
    'JSON': ('.json',),
    'KML': ('.kml',),
    'KMZ': ('.kmz',),
    'ZIP': ('.zip',),
    'PDF': ('.pdf',),
    'DOCX': ('.docx',),
}


def _read_file_bytes(file_obj) -> bytes | None:
    if file_obj is None or not hasattr(file_obj, 'read'):
        return None
    position = file_obj.tell() if hasattr(file_obj, 'tell') else None
    data = file_obj.read()
    if position is not None and hasattr(file_obj, 'seek'):
        file_obj.seek(position)
    return data


def _format_from_file(filename: str | None, file_obj=None) -> str | None:
    if not filename or '.' not in filename:
        return None
    extension = filename.rsplit('.', 1)[-1].strip().lower()
    if extension == 'zip' and file_obj is not None:
        path = None
        data = None
        if hasattr(file_obj, 'path'):
            candidate = Path(file_obj.path)
            if candidate.exists():
                path = candidate
        if path is None:
            data = _read_file_bytes(file_obj)
        inferred = infer_zip_archive_format(path=path, data=data)
        if inferred:
            return inferred
    return _EXTENSION_FORMAT_MAP.get(extension)


def _format_from_filename(filename: str | None, file_obj=None) -> str | None:
    return _format_from_file(filename, file_obj)


def _formats_from_file_specs(specs: list[tuple[str | None, Any | None]]) -> list[str]:
    merged: list[str] = []
    for name, file_obj in specs:
        fmt = _format_from_file(name, file_obj)
        if fmt and fmt not in merged:
            merged.append(fmt)
    return merged


def _resource_file_specs(dataset: Dataset) -> list[tuple[str, Any]]:
    specs = [
        (resource.file.name.rsplit('/', 1)[-1], resource.file)
        for resource in dataset.resources.all()
    ]
    if specs:
        return specs
    if dataset.source_file:
        return [(dataset.source_file.name.rsplit('/', 1)[-1], dataset.source_file)]
    return []


def _effective_resource_formats(dataset: Dataset) -> list[str]:
    return _merge_resource_formats(dataset.resource_formats, _resource_file_specs(dataset))


def _effective_resource_formats_from_values(
    resource_formats: list[str] | None,
    source_file_name: str | None,
    source_file=None,
) -> list[str]:
    specs: list[tuple[str | None, Any | None]] = []
    if source_file_name:
        specs.append((source_file_name, source_file))
    return _merge_resource_formats(resource_formats, specs)


def _merge_resource_formats(
    resource_formats: list[str] | None,
    file_specs: list[tuple[str | None, Any | None]],
) -> list[str]:
    merged = list(_normalize_formats(resource_formats))
    for fmt in _formats_from_file_specs(file_specs):
        if fmt not in merged:
            merged.append(fmt)
    if any(fmt in merged for fmt in ('SHP', 'KML')):
        merged = [fmt for fmt in merged if fmt != 'ZIP']
    return merged


def _resolve_resource_formats(
    formats: list[str] | None,
    *,
    source_file=None,
    resource_files: list | None = None,
    dataset: Dataset | None = None,
) -> list[str]:
    specs: list[tuple[str | None, Any | None]] = [
        (getattr(uploaded, 'name', None), uploaded) for uploaded in (resource_files or [])
    ]
    if source_file:
        specs.append((getattr(source_file, 'name', None), source_file))
    if dataset is not None:
        specs.extend(_resource_file_specs(dataset))
    return _merge_resource_formats(formats, specs)


def _refresh_dataset_resource_formats(
    dataset: Dataset,
    *,
    resource_files: list | None = None,
    manual_formats: list[str] | None = None,
    files_changed: bool = False,
) -> None:
    if manual_formats is not None:
        seed = manual_formats
    elif files_changed:
        seed = []
    else:
        seed = dataset.resource_formats

    formats = _resolve_resource_formats(
        seed,
        resource_files=resource_files,
        dataset=dataset,
    )
    if formats != dataset.resource_formats:
        dataset.resource_formats = formats
        dataset.save(update_fields=['resource_formats', 'updated_at'])


def _validate_resource_file(uploaded) -> None:
    if uploaded and uploaded.size > MAX_RESOURCE_FILE_BYTES:
        raise ValueError('Each file must be 50 MB or smaller.')


def parse_remove_resource_ids(raw) -> list[int]:
    if raw in (None, '', []):
        return []
    if isinstance(raw, list):
        values = raw
    elif isinstance(raw, str):
        value = raw.strip()
        if not value:
            return []
        if value.startswith('['):
            import json

            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = []
            values = parsed if isinstance(parsed, list) else [value]
        elif ',' in value:
            values = [part.strip() for part in value.split(',') if part.strip()]
        else:
            values = [value]
    else:
        values = [raw]

    ids: list[int] = []
    for item in values:
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            ids.append(parsed)
    return ids


def extract_resource_files(request) -> list:
    files: list = []
    if hasattr(request.FILES, 'getlist'):
        files = [item for item in request.FILES.getlist('resource_files') if item]
    if not files:
        source_file = request.FILES.get('source_file') if hasattr(request, 'FILES') else None
        if source_file:
            files = [source_file]
    for uploaded in files:
        _validate_resource_file(uploaded)
    return files


def _sync_primary_source_file(dataset: Dataset) -> None:
    first = dataset.resources.order_by('sort_order', 'id').first()
    dataset.source_file = first.file if first else None
    dataset.save(update_fields=['source_file', 'updated_at'])


def _attach_resource_files(dataset: Dataset, files: list) -> None:
    if not files:
        return
    start_order = dataset.resources.count()
    for offset, uploaded in enumerate(files):
        DatasetResource.objects.create(
            dataset=dataset,
            file=uploaded,
            sort_order=start_order + offset,
        )
    _sync_primary_source_file(dataset)


def _remove_dataset_resources(dataset: Dataset, resource_ids: list[int]) -> None:
    if not resource_ids:
        return
    for resource in dataset.resources.filter(pk__in=resource_ids):
        resource.file.delete(save=False)
        resource.delete()
    _sync_primary_source_file(dataset)


def _clear_dataset_resources(dataset: Dataset) -> None:
    for resource in dataset.resources.all():
        resource.file.delete(save=False)
        resource.delete()
    dataset.source_file = None


def parse_resource_formats(raw) -> list[str]:
    if raw is None or raw == '':
        return []

    if isinstance(raw, list):
        normalized: list[str] = []
        for item in raw:
            if isinstance(item, str):
                normalized.extend(parse_resource_formats(item))
            elif isinstance(item, (list, tuple)):
                for nested in item:
                    normalized.extend(parse_resource_formats(nested))
            elif item is not None:
                text = str(item).strip()
                if text:
                    normalized.append(text)
        return normalized

    if not isinstance(raw, str):
        text = str(raw).strip()
        return [text] if text else []

    value = raw.strip()
    if not value:
        return []

    if value.startswith('['):
        import ast
        import json

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return parse_resource_formats(parsed)

        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, list):
            return parse_resource_formats(parsed)

    if ',' in value and not value.startswith('{'):
        return [part.strip() for part in value.split(',') if part.strip()]

    return [value]


_SKIP_WRITE_KEYS = frozenset({'resource_files', 'remove_resource_ids', 'clear_source_file'})


def build_dataset_write_data(data) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if hasattr(data, 'getlist'):
        for key in data.keys():
            if key in _SKIP_WRITE_KEYS or key == 'resource_formats':
                continue
            value = data.get(key)
            if value not in (None, ''):
                payload[key] = value
        if 'resource_formats' in data:
            payload['resource_formats'] = parse_resource_formats(data.getlist('resource_formats'))
        return payload

    payload = dict(data)
    if 'resource_formats' in payload:
        payload['resource_formats'] = parse_resource_formats(payload.get('resource_formats'))
    return payload


def _base_queryset(*, include_inactive: bool = False) -> QuerySet[Dataset]:
    qs = Dataset.objects.select_related('governorate', 'organization').prefetch_related('resources')
    if not include_inactive:
        qs = qs.filter(is_active=True)
    return qs


def _unique_slug(title: str, exclude_id: int | None = None) -> str:
    base = slugify(title)[:200] or 'dataset'
    slug = base
    counter = 1
    while Dataset.objects.filter(slug=slug).exclude(pk=exclude_id).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


def _normalize_formats(formats: list[str] | None) -> list[str]:
    if not formats:
        return []
    seen: set[str] = set()
    normalized: list[str] = []
    for fmt in formats:
        canonical = _FORMAT_LOOKUP.get(str(fmt).strip().upper())
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        normalized.append(canonical)
    return normalized


def _apply_filters(qs: QuerySet[Dataset], params: dict[str, Any]) -> QuerySet[Dataset]:
    status = (params.get('status') or DatasetStatus.ACTIVE).strip()
    if status == DatasetStatus.ARCHIVED:
        qs = qs.filter(status=DatasetStatus.ARCHIVED)
    elif status == 'all':
        pass
    else:
        qs = qs.filter(status=DatasetStatus.ACTIVE)

    sector = (params.get('sector') or '').strip()
    sectors = params.get('sectors')
    if sectors:
        qs = qs.filter(sector__in=list(sectors))
    elif sector:
        qs = qs.filter(sector=sector)

    search = (params.get('search') or '').strip()
    if search:
        qs = qs.filter(
            Q(title_en__icontains=search)
            | Q(title_ar__icontains=search)
            | Q(description_en__icontains=search)
            | Q(description_ar__icontains=search)
            | Q(organization__name_en__icontains=search)
            | Q(organization__acronym__icontains=search)
        )

    governorate = (params.get('governorate') or '').strip()
    if governorate:
        qs = qs.filter(governorate__pcode=governorate)

    organization = (params.get('organization') or '').strip()
    if organization:
        qs = qs.filter(organization__slug=organization)

    fmt = (params.get('format') or '').strip()
    canonical = _FORMAT_LOOKUP.get(fmt.upper()) if fmt else None
    if canonical:
        format_q = Q(resource_formats__contains=[canonical])
        for suffix in _FORMAT_FILE_SUFFIXES.get(canonical, ()):
            format_q |= Q(source_file__iendswith=suffix)
            format_q |= Q(resources__file__iendswith=suffix)
        qs = qs.filter(format_q).distinct()

    return qs


def _apply_ordering(qs: QuerySet[Dataset], ordering: str | None) -> QuerySet[Dataset]:
    allowed = {
        'updated_at',
        '-updated_at',
        'title_en',
        '-title_en',
        'download_count',
        '-download_count',
        'view_count',
        '-view_count',
    }
    value = (ordering or '-updated_at').strip()
    if value not in allowed:
        value = '-updated_at'
    return qs.order_by(value)


def list_datasets(params: dict[str, Any], *, include_inactive: bool = False) -> dict[str, Any]:
    qs = _apply_ordering(_apply_filters(_base_queryset(include_inactive=include_inactive), params), params.get('ordering'))

    page = max(int(params.get('page') or 1), 1)
    page_size = min(max(int(params.get('page_size') or 10), 1), 100)
    total = qs.count()
    start = (page - 1) * page_size
    results = list(qs[start : start + page_size])

    return {
        'count': total,
        'page': page,
        'page_size': page_size,
        'results': results,
    }


def get_dataset(dataset_id: int) -> Dataset:
    return _base_queryset(include_inactive=True).get(pk=dataset_id)


def create_dataset(data: dict[str, Any], *, resource_files: list | None = None) -> Dataset:
    title_en = data['title_en']
    uploads = list(resource_files or [])
    legacy_source = data.pop('source_file', None)
    if legacy_source and legacy_source not in uploads:
        uploads.insert(0, legacy_source)
    formats = _resolve_resource_formats(
        data.get('resource_formats'),
        resource_files=uploads,
    )
    now = timezone.now()
    dataset = Dataset.objects.create(
        title_en=title_en,
        title_ar=data.get('title_ar', ''),
        slug=_unique_slug(title_en),
        description_en=data.get('description_en', ''),
        description_ar=data.get('description_ar', ''),
        organization=data['organization'],
        governorate=data['governorate'],
        sector=data['sector'],
        resource_formats=formats,
        source_file=None,
        external_url=data.get('external_url', ''),
        data_start_date=data.get('data_start_date'),
        data_end_date=data.get('data_end_date'),
        download_count=max(int(data.get('download_count') or 0), 0),
        view_count=max(int(data.get('view_count') or 0), 0),
        status=data.get('status', DatasetStatus.ACTIVE),
        is_active=data.get('is_active', True),
        created_at=now,
        updated_at=now,
    )
    _attach_resource_files(dataset, uploads)
    _refresh_dataset_resource_formats(
        dataset,
        resource_files=uploads,
        manual_formats=formats,
        files_changed=bool(uploads),
    )
    return dataset


def update_dataset(
    dataset: Dataset,
    data: dict[str, Any],
    *,
    clear_source_file: bool = False,
    resource_files: list | None = None,
    remove_resource_ids: list[int] | None = None,
) -> Dataset:
    uploads = list(resource_files or [])
    legacy_source = data.pop('source_file', None)
    if legacy_source and legacy_source not in uploads:
        uploads.insert(0, legacy_source)

    if clear_source_file:
        _clear_dataset_resources(dataset)

    if remove_resource_ids:
        _remove_dataset_resources(dataset, remove_resource_ids)

    if uploads:
        _attach_resource_files(dataset, uploads)

    if 'title_en' in data and data['title_en'] != dataset.title_en:
        dataset.slug = _unique_slug(data['title_en'], exclude_id=dataset.pk)
    for key, value in data.items():
        setattr(dataset, key, value)
    dataset.updated_at = timezone.now()
    dataset.save()
    _sync_primary_source_file(dataset)
    files_changed = bool(uploads or clear_source_file or remove_resource_ids)
    if 'resource_formats' in data or files_changed:
        _refresh_dataset_resource_formats(
            dataset,
            resource_files=uploads,
            manual_formats=data.get('resource_formats') if 'resource_formats' in data else None,
            files_changed=files_changed,
        )
    return dataset


def get_dataset_resource(dataset: Dataset, resource_id: int | None) -> DatasetResource | None:
    if resource_id:
        return dataset.resources.filter(pk=resource_id).first()
    return dataset.resources.order_by('sort_order', 'id').first()


def backfill_resource_formats() -> int:
    updated = 0
    for dataset in Dataset.objects.prefetch_related('resources'):
        formats = _effective_resource_formats(dataset)
        if not formats or formats == dataset.resource_formats:
            continue
        dataset.resource_formats = formats
        dataset.save(update_fields=['resource_formats'])
        updated += 1
    return updated


# `datasets_dataset` is owned by report_moe master_data, but view_count/download_count
# are non-critical usage counters, not core content — enforce_single_writer.sql grants
# moeds_app UPDATE on exactly these two columns (see the "Narrow exception" comment
# there). Only ever touch those two columns here: an UPDATE naming any other column
# (including `updated_at`) would fail with InsufficientPrivilege for moeds_app, since
# every other column stays report_app-only.


def record_dataset_view(dataset: Dataset) -> Dataset:
    dataset.view_count += 1
    dataset.save(update_fields=['view_count'])
    return dataset


def record_dataset_download(dataset: Dataset) -> Dataset:
    dataset.download_count += 1
    dataset.save(update_fields=['download_count'])
    return dataset


def soft_delete_dataset(dataset: Dataset) -> None:
    dataset.is_active = False
    dataset.updated_at = timezone.now()
    dataset.save(update_fields=['is_active', 'updated_at'])


def _format_counts(qs: QuerySet[Dataset]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {fmt: 0 for fmt in DATASET_FORMAT_CHOICES}
    for dataset in qs.prefetch_related('resources'):
        for fmt in _effective_resource_formats(dataset):
            if fmt in counts:
                counts[fmt] += 1
    return [
        {'value': value, 'label': value, 'count': counts[value]}
        for value in DATASET_FORMAT_CHOICES
        if counts[value] > 0
    ]


def build_datasets_meta(
    *,
    sector: str | None = None,
    sectors: list[str] | None = None,
    status: str = DatasetStatus.ACTIVE,
    governorate: str | None = None,
    format: str | None = None,
) -> dict[str, Any]:
    sector_filter: dict[str, Any] = {'sector': sector or ''}
    if sectors:
        sector_filter = {'sectors': sectors}
    active_qs = _apply_filters(_base_queryset(), {**sector_filter, 'status': DatasetStatus.ACTIVE})
    archived_qs = _apply_filters(_base_queryset(), {**sector_filter, 'status': DatasetStatus.ARCHIVED})

    facet_filter: dict[str, Any] = {
        **sector_filter,
        'governorate': governorate or '',
        'format': format or '',
    }
    if status in DatasetStatus.values:
        facet_filter['status'] = status
    elif status != 'all':
        facet_filter['status'] = DatasetStatus.ACTIVE
    facet_qs = _apply_filters(_base_queryset(), facet_filter)

    governorate_counts = (
        ProjectGovernorate.objects.annotate(
            dataset_count=Count('datasets', filter=Q(datasets__in=facet_qs)),
        )
        .order_by('id')
    )

    organization_counts = (
        ProjectOrganization.objects.annotate(
            dataset_count=Count('datasets', filter=Q(datasets__in=facet_qs)),
        )
        .order_by('name_en')
    )

    return {
        'active_count': active_qs.count(),
        'archived_count': archived_qs.count(),
        'sectors': [
            {'value': value, 'label_en': label, 'label_ar': SECTOR_LABELS_AR.get(value, label)}
            for value, label in Sector.choices
        ],
        'statuses': [
            {'value': value, 'label_en': label, 'label_ar': DATASET_STATUS_LABELS_AR.get(value, label)}
            for value, label in DatasetStatus.choices
        ],
        'format_options': [
            {'value': value, 'label_en': value, 'label_ar': value}
            for value in DATASET_FORMAT_CHOICES
        ],
        'formats': _format_counts(facet_qs),
        'governorates': list(governorate_counts),
        'organizations': list(organization_counts),
    }
