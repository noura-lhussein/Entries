from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .drinking_water_admin import drinking_water_station_lookups
from .models import (
    Dam,
    DamStorageReading,
    EuphratesCascadeReading,
    RainfallBasin,
    RainfallObservation,
    RainfallStation,
)


def _parse_date(value) -> date | None:
    if value is None or value == '':
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value) -> Decimal | None:
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None


def _parse_int(value) -> int | None:
    if value is None or value == '':
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def get_lookups() -> dict[str, Any]:
    governorates = sorted(
        Dam.objects.exclude(governorate='')
        .values_list('governorate', flat=True)
        .order_by()
        .distinct(),
    )
    rainfall_governorates = sorted(
        RainfallStation.objects.exclude(governorate='')
        .values_list('governorate', flat=True)
        .order_by()
        .distinct(),
    )
    merged_governorates = sorted(set(governorates) | set(rainfall_governorates))
    return {
        'basins': list(
            RainfallBasin.objects.order_by('name_en').values('slug', 'name_en', 'name_ar'),
        ),
        'governorates': merged_governorates,
        'dams': [
            {'id': dam.id, 'name': dam.name, 'governorate': dam.governorate}
            for dam in Dam.objects.order_by('governorate', 'name')
        ],
        'stations': [
            {
                'id': station.id,
                'name': station.name,
                'basin_slug': station.basin.slug,
                'basin_en': station.basin.name_en,
                'basin_ar': station.basin.name_ar,
                'governorate': station.governorate,
            }
            for station in RainfallStation.objects.select_related('basin').order_by(
                'basin__name_en',
                'name',
            )
        ],
        'drinking_water_stations': drinking_water_station_lookups(),
    }


def clear_rainfall_observations() -> dict[str, Any]:
    deleted, _ = RainfallObservation.objects.all().delete()
    return {
        'ok': True,
        'message_en': f'Deleted {deleted:,} rainfall observations.',
        'message_ar': f'تم حذف {deleted:,} سجل هطول.',
    }


def clear_dam_storage_readings() -> dict[str, Any]:
    deleted, _ = DamStorageReading.objects.all().delete()
    return {
        'ok': True,
        'message_en': f'Deleted {deleted:,} dam storage readings.',
        'message_ar': f'تم حذف {deleted:,} قراءة مخزون.',
    }


def clear_euphrates_readings() -> dict[str, Any]:
    deleted, _ = EuphratesCascadeReading.objects.all().delete()
    return {
        'ok': True,
        'message_en': f'Deleted {deleted:,} Euphrates daily readings.',
        'message_ar': f'تم حذف {deleted:,} قراءة يومية لسدود الفرات.',
    }


def get_euphrates_reading(reading_date: date) -> dict[str, Any] | None:
    row = EuphratesCascadeReading.objects.filter(reading_date=reading_date).first()
    if not row:
        return None
    return _serialize_euphrates(row)


def upsert_euphrates_reading(payload: dict[str, Any]) -> dict[str, Any]:
    reading_date = _parse_date(payload.get('reading_date'))
    if not reading_date:
        return {'ok': False, 'error_en': 'Valid reading_date is required.', 'error_ar': 'تاريخ القراءة مطلوب.'}

    defaults = {
        'inflow_jarabulus': _parse_decimal(payload.get('inflow_jarabulus')),
        'tishreen_level_m': _parse_decimal(payload.get('tishreen_level_m')),
        'tishreen_storage_mcm': _parse_decimal(payload.get('tishreen_storage_mcm')),
        'tishreen_outflow': _parse_decimal(payload.get('tishreen_outflow')),
        'tishreen_generation_mwh': _parse_decimal(payload.get('tishreen_generation_mwh')),
        'furat_level_m': _parse_decimal(payload.get('furat_level_m')),
        'furat_storage_mcm': _parse_decimal(payload.get('furat_storage_mcm')),
        'furat_outflow': _parse_decimal(payload.get('furat_outflow')),
        'furat_generation_mwh': _parse_decimal(payload.get('furat_generation_mwh')),
        'kadiran_outflow': _parse_decimal(payload.get('kadiran_outflow')),
        'kadiran_generation_mwh': _parse_decimal(payload.get('kadiran_generation_mwh')),
        'al_jalab_discharge': _parse_decimal(payload.get('al_jalab_discharge')),
        'total_generation_mwh': _parse_decimal(payload.get('total_generation_mwh')),
        'report_label': str(payload.get('report_label') or '').strip(),
        'source_file': 'manual-entry',
    }
    existed = EuphratesCascadeReading.objects.filter(reading_date=reading_date).exists()
    row, _ = EuphratesCascadeReading.objects.update_or_create(
        reading_date=reading_date,
        defaults=defaults,
    )
    action_en = 'Updated' if existed else 'Saved'
    action_ar = 'تم التحديث' if existed else 'تم الحفظ'
    return {
        'ok': True,
        'created': not existed,
        'message_en': f'{action_en} Euphrates reading for {reading_date.isoformat()}.',
        'message_ar': f'{action_ar} قراءة {reading_date.isoformat()}.',
        'reading': _serialize_euphrates(row),
    }


def upsert_dam_storage_reading(payload: dict[str, Any]) -> dict[str, Any]:
    reading_date = _parse_date(payload.get('reading_date'))
    dam_id = _parse_int(payload.get('dam_id'))
    if not reading_date:
        return {'ok': False, 'error_en': 'Valid reading_date is required.', 'error_ar': 'تاريخ القراءة مطلوب.'}
    if dam_id is None:
        return {'ok': False, 'error_en': 'dam_id is required.', 'error_ar': 'السد مطلوب.'}

    dam = Dam.objects.filter(pk=dam_id).first()
    if not dam:
        return {'ok': False, 'error_en': 'Dam not found.', 'error_ar': 'السد غير موجود.'}

    storage = _parse_decimal(payload.get('storage_mcm'))
    if storage is None:
        return {'ok': False, 'error_en': 'storage_mcm is required.', 'error_ar': 'حجم المخزون مطلوب.'}

    notes = str(payload.get('notes') or '').strip()
    existed = DamStorageReading.objects.filter(dam=dam, reading_date=reading_date).exists()
    row, _ = DamStorageReading.objects.update_or_create(
        dam=dam,
        reading_date=reading_date,
        defaults={'storage_mcm': storage, 'notes': notes},
    )
    action_en = 'Updated' if existed else 'Saved'
    action_ar = 'تم التحديث' if existed else 'تم الحفظ'
    return {
        'ok': True,
        'created': not existed,
        'message_en': f'{action_en} storage for {dam.name} on {reading_date.isoformat()}.',
        'message_ar': f'{action_ar} مخزون {dam.name} بتاريخ {reading_date.isoformat()}.',
        'reading': {
            'dam_id': dam.id,
            'dam_name': dam.name,
            'governorate': dam.governorate,
            'reading_date': row.reading_date.isoformat(),
            'storage_mcm': _float(row.storage_mcm),
            'notes': row.notes,
        },
    }


def upsert_rainfall_observation(payload: dict[str, Any]) -> dict[str, Any]:
    reading_date = _parse_date(payload.get('observation_date'))
    basin_slug = str(payload.get('basin_slug') or '').strip()
    station_name = str(payload.get('station_name') or '').strip()
    if not reading_date or not basin_slug or not station_name:
        return {
            'ok': False,
            'error_en': 'observation_date, basin_slug, and station_name are required.',
            'error_ar': 'التاريخ والحوض واسم المحطة مطلوبة.',
        }

    basin = RainfallBasin.objects.filter(slug=basin_slug).first()
    if not basin:
        return {'ok': False, 'error_en': 'Basin not found.', 'error_ar': 'الحوض غير موجود.'}

    governorate = str(payload.get('governorate') or '').strip()
    precipitation = _parse_decimal(payload.get('precipitation_mm'))
    if precipitation is None:
        precipitation = Decimal('0')
    notes = str(payload.get('notes') or '').strip()

    station, _ = RainfallStation.objects.get_or_create(
        basin=basin,
        name=station_name,
        defaults={'governorate': governorate},
    )
    if governorate and station.governorate != governorate:
        station.governorate = governorate
        station.save(update_fields=['governorate'])

    existed = RainfallObservation.objects.filter(station=station, observation_date=reading_date).exists()
    row, _ = RainfallObservation.objects.update_or_create(
        station=station,
        observation_date=reading_date,
        defaults={'precipitation_mm': precipitation, 'notes': notes},
    )
    action_en = 'Updated' if existed else 'Saved'
    action_ar = 'تم التحديث' if existed else 'تم الحفظ'
    return {
        'ok': True,
        'created': not existed,
        'message_en': f'{action_en} rainfall for {station.name} on {reading_date.isoformat()}.',
        'message_ar': f'{action_ar} هطول {station.name} بتاريخ {reading_date.isoformat()}.',
        'observation': {
            'basin_slug': basin.slug,
            'station_name': station.name,
            'governorate': station.governorate,
            'observation_date': row.observation_date.isoformat(),
            'precipitation_mm': _float(row.precipitation_mm),
            'notes': row.notes,
        },
    }


def _serialize_euphrates(row: EuphratesCascadeReading) -> dict[str, Any]:
    return {
        'reading_date': row.reading_date.isoformat(),
        'inflow_jarabulus': _float(row.inflow_jarabulus),
        'tishreen_level_m': _float(row.tishreen_level_m),
        'tishreen_storage_mcm': _float(row.tishreen_storage_mcm),
        'tishreen_outflow': _float(row.tishreen_outflow),
        'tishreen_generation_mwh': _float(row.tishreen_generation_mwh),
        'furat_level_m': _float(row.furat_level_m),
        'furat_storage_mcm': _float(row.furat_storage_mcm),
        'furat_outflow': _float(row.furat_outflow),
        'furat_generation_mwh': _float(row.furat_generation_mwh),
        'kadiran_outflow': _float(row.kadiran_outflow),
        'kadiran_generation_mwh': _float(row.kadiran_generation_mwh),
        'al_jalab_discharge': _float(row.al_jalab_discharge),
        'total_generation_mwh': _float(row.total_generation_mwh),
        'report_label': row.report_label,
    }
