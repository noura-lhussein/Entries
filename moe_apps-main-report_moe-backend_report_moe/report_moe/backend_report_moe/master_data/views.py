"""DRF views for master-data registry CRUD (session auth)."""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import gis as gis_admin
from .audit import log_master_data_change
from .exceptions import MasterDataError
from .permissions import (
    IsAuthenticatedMasterData,
    _is_full_admin,
    require_sector,
    user_allowed_sectors,
)
from .registry import get_resource_spec, registry_payload
from .serialization import (
    apply_model_update,
    model_to_admin_dict,
    model_to_dict,
    requires_client_pk,
)

logger = logging.getLogger(__name__)

# The moeds-owned master tables live behind this alias (search_path=moeds,public).

_AUDIT_SKIP = frozenset({
    'id',
    'pk',
    'created_at',
    'updated_at',
    'created_by',
    'updated_by',
    'created_by_id',
    'updated_by_id',
    'built_at',
})


def _writable_payload(
    payload: dict[str, Any],
    *,
    locked: tuple[str, ...] = (),
    hidden: tuple[str, ...] = (),
    allow_pk: bool = False,
) -> dict[str, Any]:
    # `hidden` fields are excluded from the field schema, so the UI never offers them —
    # strip them here too, otherwise a hand-rolled request can still set them
    # (e.g. datasets.download_count / view_count).
    skip = _AUDIT_SKIP | set(locked) | set(hidden)
    if allow_pk:
        skip = skip - {'id', 'pk'}
    return {k: v for k, v in payload.items() if k not in skip}


def _validation_error_message(exc: DjangoValidationError) -> str:
    if hasattr(exc, 'message_dict'):
        parts = []
        for field, messages in exc.message_dict.items():
            joined = '; '.join(str(m) for m in messages)
            parts.append(f'{field}: {joined}')
        return ' '.join(parts) or str(exc)
    if hasattr(exc, 'messages'):
        return ' '.join(str(m) for m in exc.messages)
    return str(exc)


def _error_response(exc: Exception) -> Response:
    if isinstance(exc, MasterDataError):
        return Response({'detail': exc.message}, status=exc.status)
    if isinstance(exc, DjangoValidationError):
        return Response({'detail': _validation_error_message(exc)}, status=400)
    if isinstance(exc, ProtectedError):
        return Response(
            {'detail': 'لا يمكن الحذف: السجل مرتبط بسجلات أخرى.'},
            status=status.HTTP_409_CONFLICT,
        )
    if isinstance(exc, IntegrityError):
        logger.warning('master_data integrity error: %s', exc)
        return Response(
            {'detail': 'تعارض في البيانات — تحقق من القيم الفريدة والمراجع.'},
            status=status.HTTP_409_CONFLICT,
        )
    logger.exception('master_data unexpected error')
    return Response({'detail': str(exc)}, status=400)


def _object_error_response(exc: Exception) -> Response:
    """Map a per-object failure to a status. Only a genuine miss is a 404.

    Previously every exception here became `404 Not found.`, which hid ProtectedError
    (deleting a referenced row), IntegrityError, and DB connectivity failures.
    """
    if 'DoesNotExist' in type(exc).__name__:
        return Response({'detail': 'Not found.'}, status=404)
    return _error_response(exc)


def _apply_server_timestamps(instance, *, creating: bool) -> None:
    """Fill created_at / updated_at that the client is not allowed to set.

    `datasets_dataset` and `datasets_datasetresource` declare these as plain
    DateTimeFields (no auto_now / auto_now_add) over NOT NULL columns with no database
    default. Since `_AUDIT_SKIP` strips them from the payload, a create would otherwise
    always fail full_clean() with "cannot be null".
    """
    now = timezone.now()
    names = {f.name: f for f in instance._meta.fields}
    for name, creating_only in (('created_at', True), ('updated_at', False)):
        field = names.get(name)
        if field is None:
            continue
        if getattr(field, 'auto_now', False) or getattr(field, 'auto_now_add', False):
            continue  # Django manages it
        if creating_only and not creating:
            continue
        if creating_only and getattr(instance, name, None) is not None:
            continue  # preserve an existing created_at
        setattr(instance, name, now)


def _admin_save(
    instance,
    payload: dict[str, Any],
    *,
    partial: bool,
    locked: tuple[str, ...] = (),
    hidden: tuple[str, ...] = (),
):
    creating = instance.pk is None or not partial
    # Models whose PK is neither auto nor defaulted can only be created if the client
    # supplies the id (see serialization.requires_client_pk).
    allow_pk = creating and requires_client_pk(type(instance))
    apply_model_update(
        instance,
        _writable_payload(payload, locked=locked, hidden=hidden, allow_pk=allow_pk),
        partial=partial,
        allow_pk=allow_pk,
    )
    _apply_server_timestamps(instance, creating=creating)
    try:
        instance.full_clean()
    except DjangoValidationError as exc:
        raise MasterDataError(_validation_error_message(exc), status=400) from exc
    instance.save()
    return instance


def _base_queryset(spec):
    assert spec.model is not None
    qs = spec.model.objects.all()
    if spec.queryset_filters:
        qs = qs.filter(**spec.queryset_filters)
    return qs


def _get_admin_object(spec, pk: str):
    qs = _base_queryset(spec)
    return qs.get(pk=pk)


def _option_label(row) -> str:
    for attr in ('name_ar', 'name_en', 'name', 'refinery_name', 'well_code', 'code', 'slug'):
        val = getattr(row, attr, None)
        if val is not None and str(val).strip():
            return str(val).strip()
    return str(row)


class MasterDataRegistryView(APIView):
    permission_classes = [IsAuthenticatedMasterData]

    def get(self, request: Request) -> Response:
        sectors = user_allowed_sectors(request.user, write=False)
        # Write-only access also implies view for that sector
        sectors |= user_allowed_sectors(request.user, write=True)
        if _is_full_admin(request.user):
            return Response(registry_payload())
        return Response(registry_payload(allowed_sectors=sectors))


class MasterDataOptionsView(APIView):
    permission_classes = [IsAuthenticatedMasterData]

    def get(self, request: Request, slug: str) -> Response:
        spec = get_resource_spec(slug)
        if not spec:
            return Response({'detail': 'Unknown resource.'}, status=404)
        require_sector(request.user, spec.sector, write=False)
        if spec.gis_layer_id or spec.model is None:
            return Response({'options': []})
        options = []
        for row in _base_queryset(spec)[:300]:
            options.append({'value': row.pk, 'label': _option_label(row)})
        return Response({'options': options})


class MasterDataListCreateView(APIView):
    permission_classes = [IsAuthenticatedMasterData]

    def get(self, request: Request, slug: str) -> Response:
        spec = get_resource_spec(slug)
        if not spec:
            return Response({'detail': 'Unknown resource.'}, status=404)
        require_sector(request.user, spec.sector, write=False)

        search = (request.query_params.get('search') or '').strip()
        status_filter = (request.query_params.get('status') or '').strip()
        sort_col = (request.query_params.get('sort') or '').strip()
        sort_dir = (request.query_params.get('direction') or 'asc').lower()
        try:
            page = max(1, int(request.query_params.get('page') or 1))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(max(1, int(request.query_params.get('page_size') or 50)), 100)
        except (TypeError, ValueError):
            page_size = 50

        if spec.gis_layer_id:
            try:
                payload = gis_admin.list_features(
                    spec.gis_layer_id,
                    search=search,
                    page=page,
                    page_size=page_size,
                    sort=sort_col,
                    direction=sort_dir,
                )
            except MasterDataError as exc:
                return _error_response(exc)
            payload['slug'] = spec.slug
            return Response(payload)

        if spec.model is None:
            return Response({'detail': 'Unknown resource.'}, status=404)

        qs = _base_queryset(spec)
        allowed_fields = {f.name for f in spec.model._meta.fields}

        if status_filter and 'status' in allowed_fields:
            qs = qs.filter(status=status_filter)

        if search:
            fields = spec.search_fields or tuple(
                f.name
                for f in spec.model._meta.fields
                if f.get_internal_type() in ('CharField', 'TextField', 'SlugField')
            )[:6]
            q = Q()
            for fname in fields:
                q |= Q(**{f'{fname}__icontains': search})
            if q:
                qs = qs.filter(q)

        if sort_col in allowed_fields and sort_col in spec.list_display:
            ordering = [f'-{sort_col}' if sort_dir == 'desc' else sort_col]
        elif spec.default_sort_column and spec.default_sort_column in allowed_fields:
            col = spec.default_sort_column
            ordering = [f'-{col}' if spec.default_sort_direction == 'desc' else col]
        else:
            ordering = list(spec.model._meta.ordering or ['pk'])

        qs = qs.order_by(*ordering)
        total_count = qs.count()
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = min(page, total_pages)
        offset = (page - 1) * page_size
        rows = list(qs[offset : offset + page_size])

        # Prefetch FK labels for wells/rainfall stations
        fk_names = [f.name for f in spec.model._meta.fields if f.is_relation]
        if fk_names:
            results = [model_to_admin_dict(row) for row in rows]
        else:
            results = [model_to_dict(row) for row in rows]

        return Response(
            {
                'slug': spec.slug,
                'count': len(results),
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'results': results,
            }
        )

    def post(self, request: Request, slug: str) -> Response:
        spec = get_resource_spec(slug)
        if not spec:
            return Response({'detail': 'Unknown resource.'}, status=404)
        require_sector(request.user, spec.sector, write=True)
        if spec.read_only:
            return Response({'detail': 'This resource is read-only.'}, status=405)

        body = dict(request.data)
        for key, value in spec.default_create_values.items():
            body.setdefault(key, value)

        try:
            # Writes go through the single default connection —
            # an atomic block on `default` would not cover them.
            with transaction.atomic():
                if spec.gis_layer_id:
                    row = gis_admin.create_feature(spec.gis_layer_id, body)
                    log_master_data_change(
                        user=request.user, action='create', slug=spec.slug, pk=row.get('id'),
                        payload=body, request=request,
                    )
                    return Response(row, status=status.HTTP_201_CREATED)
                if spec.model is None:
                    return Response({'detail': 'Unknown resource.'}, status=404)
                instance = _admin_save(
                    spec.model(), body, partial=False,
                    locked=spec.locked_fields, hidden=spec.hidden_fields,
                )
                log_master_data_change(
                    user=request.user, action='create', slug=spec.slug, pk=instance.pk,
                    payload=body, request=request,
                )
                return Response(model_to_admin_dict(instance), status=status.HTTP_201_CREATED)
        except Exception as exc:
            return _error_response(exc)


class MasterDataDetailView(APIView):
    permission_classes = [IsAuthenticatedMasterData]

    def get(self, request: Request, slug: str, pk: str) -> Response:
        spec = get_resource_spec(slug)
        if not spec:
            return Response({'detail': 'Unknown resource.'}, status=404)
        require_sector(request.user, spec.sector, write=False)
        try:
            if spec.gis_layer_id:
                return Response(gis_admin.get_feature(spec.gis_layer_id, pk))
            instance = _get_admin_object(spec, pk)
            return Response(model_to_admin_dict(instance))
        except MasterDataError as exc:
            return _error_response(exc)
        except Exception as exc:
            return _object_error_response(exc)

    def patch(self, request: Request, slug: str, pk: str) -> Response:
        spec = get_resource_spec(slug)
        if not spec:
            return Response({'detail': 'Unknown resource.'}, status=404)
        require_sector(request.user, spec.sector, write=True)
        if spec.read_only:
            return Response({'detail': 'This resource is read-only.'}, status=405)
        body = dict(request.data)
        try:
            with transaction.atomic():
                if spec.gis_layer_id:
                    before = gis_admin.get_feature(spec.gis_layer_id, pk)
                    row = gis_admin.update_feature(spec.gis_layer_id, pk, body)
                    log_master_data_change(
                        user=request.user, action='update', slug=spec.slug, pk=pk,
                        payload=body, before=before, request=request,
                    )
                    return Response(row)
                instance = _get_admin_object(spec, pk)
                before = model_to_dict(instance)
                instance = _admin_save(
                    instance, body, partial=True,
                    locked=spec.locked_fields, hidden=spec.hidden_fields,
                )
                log_master_data_change(
                    user=request.user, action='update', slug=spec.slug, pk=instance.pk,
                    payload=body, before=before, request=request,
                )
                return Response(model_to_admin_dict(instance))
        except MasterDataError as exc:
            return _error_response(exc)
        except Exception as exc:
            return _object_error_response(exc)

    def delete(self, request: Request, slug: str, pk: str) -> Response:
        spec = get_resource_spec(slug)
        if not spec:
            return Response({'detail': 'Unknown resource.'}, status=404)
        require_sector(request.user, spec.sector, write=True)
        if spec.read_only:
            return Response({'detail': 'This resource is read-only.'}, status=405)
        try:
            with transaction.atomic():
                if spec.gis_layer_id:
                    before = gis_admin.get_feature(spec.gis_layer_id, pk)
                    gis_admin.delete_feature(spec.gis_layer_id, pk)
                    log_master_data_change(
                        user=request.user, action='delete', slug=spec.slug, pk=pk,
                        payload=before, request=request,
                    )
                    return Response(status=status.HTTP_204_NO_CONTENT)
                instance = _get_admin_object(spec, pk)
                # Snapshot before the row is gone — a delete audit with no values is useless.
                before = model_to_dict(instance)
                instance.delete()
                log_master_data_change(
                    user=request.user, action='delete', slug=spec.slug, pk=pk,
                    payload=before, request=request,
                )
                return Response(status=status.HTTP_204_NO_CONTENT)
        except MasterDataError as exc:
            return _error_response(exc)
        except Exception as exc:
            return _object_error_response(exc)


class MasterDataEntitySlugView(APIView):
    """Resolve Form Builder entity attr type → admin resource slug."""

    permission_classes = [IsAuthenticatedMasterData]

    def get(self, request: Request, entity_type: str) -> Response:
        from .permissions import user_can_access_sector
        from .registry import get_resource_by_entity_type

        spec = get_resource_by_entity_type(entity_type)
        if not spec:
            return Response({'detail': 'Unknown entity type.'}, status=404)
        require_sector(request.user, spec.sector, write=False)
        return Response(
            {
                'entity_type': entity_type,
                'slug': spec.slug,
                'label_ar': spec.label_ar,
                'label_en': spec.label_en,
                'can_write': user_can_access_sector(request.user, spec.sector, write=True),
            }
        )
