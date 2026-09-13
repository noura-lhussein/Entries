"""Blank Excel template download and upload import for electricity daily reports."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from django.http import HttpResponse
from water.template_generator import multisheet_xlsx_response

from .report_export import build_electricity_report_sheets_from_source
from .services import import_extracted_row
from .xlsx_extract import extract_xlsx


def build_electricity_blank_template_sheets(sample_date: date | None = None) -> dict[str, list[list[Any]]]:
    report_date = sample_date or date.today()
    source: dict[str, Any] = {
        'report_date': report_date.isoformat(),
        'metrics': [],
        'governorate_loads': [],
        'hydro_readings': [],
        'fuel_tank_readings': [],
        'generation_unit_readings': [],
        'generation_incidents': [],
        'grid_incidents': [],
        'maintenance_groups_ar': '',
        'notes_ar': '',
        'peak_generation_time': None,
    }
    return build_electricity_report_sheets_from_source(source)


def export_electricity_report_template_xlsx(sample_date: date | None = None) -> HttpResponse:
    sheets = build_electricity_blank_template_sheets(sample_date)
    filename = 'electricity_daily_report_template.xlsx'
    return multisheet_xlsx_response(filename, sheets)


def import_electricity_report_upload(
    uploaded,
    *,
    publish: bool = True,
) -> dict[str, Any]:
    suffix = Path(getattr(uploaded, 'name', '') or 'upload.xlsx').suffix.lower() or '.xlsx'
    if suffix not in ('.xlsx', '.xlsm'):
        return {'ok': False, 'error': 'Only .xlsx files are supported.'}

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        row = extract_xlsx(tmp_path)
        row['source_file'] = getattr(uploaded, 'name', '') or ''
        if not row.get('report_date'):
            return {'ok': False, 'error': 'Could not read report date from the workbook.'}
        report = import_extracted_row(row, publish=publish)
    except Exception as exc:  # noqa: BLE001
        return {'ok': False, 'error': str(exc)}
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        'ok': True,
        'id': report.id,
        'report_date': report.report_date.isoformat(),
        'status': report.status,
    }
