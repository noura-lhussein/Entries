from __future__ import annotations

import shutil
import tempfile
import zipfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Max

from .drinking_water_admin import drinking_water_import_status
from .drinking_water_import import import_drinking_water_workbook
from .drinking_water_survey_import import import_drinking_water_survey_workbook
from .map_layers import sync_drinking_water_map_layer
from .models import (
    Dam,
    DamStorageReading,
    EuphratesCascadeReading,
    RainfallBasin,
    RainfallObservation,
    RainfallStation,
)


def _save_uploaded_files(uploaded_files) -> Path:
    root = Path(tempfile.mkdtemp(prefix='moe-water-import-'))
    for uploaded in uploaded_files:
        name = Path(uploaded.name).name
        if name.lower().endswith('.zip'):
            zip_path = root / name
            with zip_path.open('wb') as handle:
                for chunk in uploaded.chunks():
                    handle.write(chunk)
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(root)
            zip_path.unlink(missing_ok=True)
            continue

        dest = root / name
        with dest.open('wb') as handle:
            for chunk in uploaded.chunks():
                handle.write(chunk)
    return root


def _cleanup_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def get_water_import_status() -> dict:
    rainfall_latest = RainfallObservation.objects.aggregate(latest=Max('observation_date'))['latest']
    dam_latest = DamStorageReading.objects.aggregate(latest=Max('reading_date'))['latest']
    euph_latest = EuphratesCascadeReading.objects.aggregate(latest=Max('reading_date'))['latest']

    rainfall_years = sorted(
        {
            d.year
            for d in RainfallObservation.objects.dates('observation_date', 'year')
        },
        reverse=True,
    )
    dam_years = sorted(
        {
            d.year
            for d in DamStorageReading.objects.dates('reading_date', 'year')
        },
        reverse=True,
    )
    euph_months = sorted(
        {d.strftime('%Y-%m') for d in EuphratesCascadeReading.objects.dates('reading_date', 'month')},
        reverse=True,
    )

    return {
        'rainfall': {
            'basins': RainfallBasin.objects.count(),
            'stations': RainfallStation.objects.count(),
            'observations': RainfallObservation.objects.count(),
            'latest_date': rainfall_latest.isoformat() if rainfall_latest else None,
            'year_from': rainfall_years[-1] if rainfall_years else None,
            'year_to': rainfall_years[0] if rainfall_years else None,
        },
        'dams': {
            'dams': Dam.objects.count(),
            'readings': DamStorageReading.objects.count(),
            'latest_date': dam_latest.isoformat() if dam_latest else None,
            'year_from': dam_years[-1] if dam_years else None,
            'year_to': dam_years[0] if dam_years else None,
        },
        'euphrates': {
            'readings': EuphratesCascadeReading.objects.count(),
            'latest_date': euph_latest.isoformat() if euph_latest else None,
            'months': euph_months[:12],
        },
        'drinking_water': drinking_water_import_status(),
    }


def import_rainfall_upload(uploaded_files, *, clear: bool = False) -> dict:
    if not uploaded_files:
        return {'ok': False, 'error_en': 'No files uploaded.', 'error_ar': 'لم تُرفع أي ملفات.'}

    root = _save_uploaded_files(uploaded_files)
    output = StringIO()
    try:
        call_command(
            'import_rainfall_data',
            path=str(root),
            clear=clear,
            stdout=output,
            stderr=output,
        )
    except CommandError as exc:
        return {'ok': False, 'error_en': str(exc), 'error_ar': str(exc)}
    finally:
        _cleanup_dir(root)

    after = RainfallObservation.objects.count()
    if clear:
        msg_en = f'All rainfall observations replaced ({after:,} rows now in database).'
        msg_ar = f'تم استبدال جميع سجلات الهطول ({after:,} سجل في القاعدة).'
    else:
        msg_en = (
            f'Rainfall import merged with existing data ({after:,} observations total). '
            f'Matching station + date rows were updated.'
        )
        msg_ar = (
            f'تم دمج استيراد الهطول مع البيانات الحالية ({after:,} سجل إجمالاً). '
            f'تم تحديث الصفوف المتطابقة (محطة + تاريخ).'
        )
    return {
        'ok': True,
        'message_en': msg_en,
        'message_ar': msg_ar,
        'observations': after,
        'output': output.getvalue(),
        'cleared': clear,
    }


def import_dam_upload(uploaded_files, *, clear: bool = False) -> dict:
    if not uploaded_files:
        return {'ok': False, 'error_en': 'No files uploaded.', 'error_ar': 'لم تُرفع أي ملفات.'}

    root = _save_uploaded_files(uploaded_files)
    output = StringIO()
    try:
        call_command(
            'import_dam_data',
            path=str(root),
            clear=clear,
            stdout=output,
            stderr=output,
        )
    except CommandError as exc:
        return {'ok': False, 'error_en': str(exc), 'error_ar': str(exc)}
    finally:
        _cleanup_dir(root)

    after = DamStorageReading.objects.count()
    if clear:
        msg_en = f'All dam storage readings replaced ({after:,} rows now in database).'
        msg_ar = f'تم استبدال جميع قراءات المخزون ({after:,} قراءة في القاعدة).'
    else:
        msg_en = (
            f'Dam import merged with existing data ({after:,} readings total). '
            f'Matching dam + date rows were updated.'
        )
        msg_ar = (
            f'تم دمج استيراد السدود مع البيانات الحالية ({after:,} قراءة إجمالاً). '
            f'تم تحديث الصفوف المتطابقة (سد + تاريخ).'
        )
    return {
        'ok': True,
        'message_en': msg_en,
        'message_ar': msg_ar,
        'readings': after,
        'dams': Dam.objects.count(),
        'output': output.getvalue(),
        'cleared': clear,
    }


def import_euphrates_upload(uploaded_files, *, clear: bool = False) -> dict:
    if not uploaded_files:
        return {'ok': False, 'error_en': 'No files uploaded.', 'error_ar': 'لم تُرفع أي ملفات.'}

    root = _save_uploaded_files(uploaded_files)
    output = StringIO()
    try:
        call_command(
            'import_euphrates_cascade',
            path=str(root),
            clear=clear,
            stdout=output,
            stderr=output,
        )
    except CommandError as exc:
        return {'ok': False, 'error_en': str(exc), 'error_ar': str(exc)}
    finally:
        _cleanup_dir(root)

    after = EuphratesCascadeReading.objects.count()
    if clear:
        msg_en = f'All Euphrates readings replaced ({after:,} rows now in database).'
        msg_ar = f'تم استبدال جميع قراءات الفرات ({after:,} قراءة في القاعدة).'
    else:
        msg_en = (
            f'Euphrates import merged with existing data ({after:,} readings total). '
            f'Matching dates were updated.'
        )
        msg_ar = (
            f'تم دمج استيراد الفرات مع البيانات الحالية ({after:,} قراءة إجمالاً). '
            f'تم تحديث التواريخ المتطابقة.'
        )
    return {
        'ok': True,
        'message_en': msg_en,
        'message_ar': msg_ar,
        'readings': after,
        'output': output.getvalue(),
        'cleared': clear,
    }


def import_drinking_water_geo_upload(uploaded_files, *, clear: bool = False) -> dict:
    if not uploaded_files:
        return {'ok': False, 'error_en': 'No files uploaded.', 'error_ar': 'لم تُرفع أي ملفات.'}
    if len(uploaded_files) != 1:
        return {
            'ok': False,
            'error_en': 'Upload one geo registry .xlsx file.',
            'error_ar': 'ارفع ملف سجل المحطات الجغرافي (.xlsx) واحداً فقط.',
        }

    root = _save_uploaded_files(uploaded_files)
    xlsx_files = list(root.rglob('*.xlsx'))
    if not xlsx_files:
        _cleanup_dir(root)
        return {'ok': False, 'error_en': 'No .xlsx file found.', 'error_ar': 'لم يُعثر على ملف .xlsx.'}

    try:
        stats = import_drinking_water_workbook(xlsx_files[0], clear=clear)
        sync_stats = sync_drinking_water_map_layer()
    except Exception as exc:
        return {'ok': False, 'error_en': str(exc), 'error_ar': str(exc)}
    finally:
        _cleanup_dir(root)

    msg_en = (
        f'Geo registry import complete: {stats["created"]} created, {stats["updated"]} updated, '
        f'{stats["skipped"]} skipped. Map layer synced: {sync_stats["imported"]} features.'
    )
    msg_ar = (
        f'اكتمل استيراد السجل الجغرافي: {stats["created"]} جديد، {stats["updated"]} محدّث، '
        f'{stats["skipped"]} متخطى. طبقة الخريطة: {sync_stats["imported"]} محطة.'
    )
    return {'ok': True, 'message_en': msg_en, 'message_ar': msg_ar, **stats, 'cleared': clear, **sync_stats}


def import_drinking_water_survey_upload(uploaded_files) -> dict:
    if not uploaded_files:
        return {'ok': False, 'error_en': 'No files uploaded.', 'error_ar': 'لم تُرفع أي ملفات.'}
    if len(uploaded_files) != 1:
        return {
            'ok': False,
            'error_en': 'Upload one TEI survey .xlsx file.',
            'error_ar': 'ارفع ملف استمارة TEI (.xlsx) واحداً فقط.',
        }

    root = _save_uploaded_files(uploaded_files)
    xlsx_files = list(root.rglob('*.xlsx'))
    if not xlsx_files:
        _cleanup_dir(root)
        return {'ok': False, 'error_en': 'No .xlsx file found.', 'error_ar': 'لم يُعثر على ملف .xlsx.'}

    try:
        stats = import_drinking_water_survey_workbook(xlsx_files[0])
        sync_stats = sync_drinking_water_map_layer()
    except Exception as exc:
        return {'ok': False, 'error_en': str(exc), 'error_ar': str(exc)}
    finally:
        _cleanup_dir(root)

    msg_en = (
        f'Survey import complete: {stats["updated"]} stations updated, '
        f'{stats["missing"]} TEI ids not found, {stats["skipped"]} rows skipped. '
        f'Map layer synced: {sync_stats["imported"]} features.'
    )
    msg_ar = (
        f'اكتمل استيراد الاستمارة: {stats["updated"]} محطة محدّثة، '
        f'{stats["missing"]} معرف TEI غير موجود، {stats["skipped"]} صف متخطى. '
        f'طبقة الخريطة: {sync_stats["imported"]} محطة.'
    )
    return {'ok': True, 'message_en': msg_en, 'message_ar': msg_ar, **stats, **sync_stats}
