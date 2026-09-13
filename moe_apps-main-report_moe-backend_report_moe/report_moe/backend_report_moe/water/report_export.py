"""Water dashboard per-section executive export (Excel)."""

from __future__ import annotations

from typing import Any

from config.api_errors import detail_error
from django.http import HttpResponse

from .drinking_water_dashboard import build_drinking_water_dashboard_payload
from .info_dashboard import (
    build_dams_info_dashboard as build_dams_dashboard_payload,
)
from .info_dashboard import (
    build_euphrates_info_dashboard as build_euphrates_dashboard_payload,
)
from .info_dashboard import (
    build_rainfall_info_dashboard as build_rainfall_dashboard_payload,
)
from .template_generator import multisheet_xlsx_response

WATER_EXPORT_SECTIONS = frozenset({'rainfall', 'dams', 'euphrates', 'drinking-water'})


def _fmt(value: Any) -> str | int | float:
    if value is None:
        return '—'
    if isinstance(value, float):
        if value == int(value):
            return int(value)
        return round(value, 3)
    return value


def _kpi_sheet(title: str, payload: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [
        [title],
        ['المؤشر', 'Indicator', 'القيمة', 'Value', 'الوحدة', 'Unit', 'التغير %', 'Delta %'],
    ]
    for kpi in payload.get('kpis') or []:
        rows.append(
            [
                kpi.get('label_ar') or '',
                kpi.get('label_en') or '',
                _fmt(kpi.get('value')),
                _fmt(kpi.get('value')),
                kpi.get('unit') or '',
                kpi.get('unit') or '',
                _fmt(kpi.get('delta_pct')),
                _fmt(kpi.get('delta_pct')),
            ]
        )
    return rows


def _insights_rows(payload: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [['الملاحظات', 'Insights'], ['عربي', 'English']]
    for insight in payload.get('insights') or []:
        rows.append([insight.get('text_ar') or '', insight.get('text_en') or ''])
    if len(rows) == 2:
        rows.append(['—', '—'])
    return rows


def _rainfall_sheets(*, year: int | None, basin: str | None, governorate: str | None) -> dict[str, list[list[Any]]]:
    payload = build_rainfall_dashboard_payload(
        year=year, basin_slug=basin, governorate=governorate,
    ) or {}
    period = payload.get('selected_year') or year or 'latest'
    kpis = _kpi_sheet(f'مؤشرات الأمطار — {period}', payload)
    stations: list[list[Any]] = [
        ['أعلى المحطات', 'Top stations'],
        ['المحطة', 'Station', 'الهطول (مم)', 'Total mm'],
    ]
    # Info-sourced rows carry a single bilingual-agnostic `name`, not
    # separate name_ar/name_en columns (unlike the retired legacy builder).
    for row in (payload.get('charts') or {}).get('top_stations') or []:
        name = row.get('name') or ''
        stations.append([name, name, _fmt(row.get('total_mm')), _fmt(row.get('total_mm'))])
    monthly: list[list[Any]] = [['التوزيع الشهري', 'Monthly distribution'], ['الشهر', 'Month', 'مم', 'mm']]
    monthly_values = ((payload.get('charts') or {}).get('monthly_distribution') or {}).get('values') or []
    month_labels = [
        'كانون 2', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران',
        'تموز', 'آب', 'أيلول', 'تشرين 1', 'تشرين 2', 'كانون 1',
    ]
    for index, value in enumerate(monthly_values):
        label = month_labels[index] if index < len(month_labels) else str(index + 1)
        monthly.append([label, index + 1, _fmt(value), _fmt(value)])
    return {
        'KPIs': kpis,
        'TopStations': stations,
        'Monthly': monthly,
        'Insights': _insights_rows(payload),
    }


def _dams_sheets(*, year: int | None, governorate: str | None) -> dict[str, list[list[Any]]]:
    if governorate:
        # build_dams_info_dashboard() doesn't support governorate scoping yet
        # (known gap — see water/info_dashboard.py:build_dams_info_dashboard).
        raise detail_error(
            'Dams export does not yet support governorate filtering on the Info-based dashboard.',
        )
    payload = build_dams_dashboard_payload(year=year, governorate=None) or {}
    period = payload.get('selected_year') or year or 'latest'
    kpis = _kpi_sheet(f'مؤشرات السدود — {period}', payload)
    top: list[list[Any]] = [
        ['أعلى السدود مخزوناً', 'Top dams by storage'],
        ['السد', 'Dam', 'المخزون (مليون م٣)', 'Storage MCM'],
    ]
    for row in (payload.get('charts') or {}).get('top_dams') or []:
        name = row.get('name') or ''
        top.append([name, name, _fmt(row.get('storage_mcm')), _fmt(row.get('storage_mcm'))])
    return {
        'KPIs': kpis,
        'TopDams': top,
        'Insights': _insights_rows(payload),
    }


def _euphrates_sheets(*, month: str | None) -> dict[str, list[list[Any]]]:
    payload = build_euphrates_dashboard_payload(month=month) or {}
    period = payload.get('selected_month') or month or 'latest'
    kpis = _kpi_sheet(f'مؤشرات الفرات — {period}', payload)
    summary: list[list[Any]] = [['ملخص الشهر', 'Month summary'], ['البند', 'Item', 'القيمة', 'Value', 'الوحدة', 'Unit']]
    for key, block in (payload.get('month_summary') or {}).items():
        if not isinstance(block, dict):
            continue
        summary.append(
            [
                block.get('label_ar') or key,
                block.get('label_en') or key,
                _fmt(block.get('value')),
                _fmt(block.get('value')),
                block.get('unit') or '',
                block.get('unit') or '',
            ]
        )
    dams: list[list[Any]] = [
        ['السدود', 'Dams'],
        [
            'السد', 'Dam', 'المنسوب', 'Level', 'التخزين مليار م٣', 'Storage BCM',
            'التصريف', 'Outflow', 'التوليد', 'Generation', 'نسبة الامتلاء', 'Fill %',
        ],
    ]
    for dam in payload.get('dams') or []:
        # Info-sourced euphrates dams carry `outflow` (not `outflow_m3s`) and
        # no precomputed `fill_pct` — derive it from storage/max_storage when
        # both are present, matching what the legacy builder used to show.
        storage_bcm = dam.get('storage_bcm')
        max_storage_bcm = dam.get('max_storage_bcm')
        fill_pct = (
            round(storage_bcm / max_storage_bcm * 100, 1)
            if storage_bcm is not None and max_storage_bcm
            else None
        )
        dams.append(
            [
                dam.get('name_ar') or dam.get('name_en') or '',
                dam.get('name_en') or dam.get('name_ar') or '',
                _fmt(dam.get('level_m')),
                _fmt(dam.get('level_m')),
                _fmt(storage_bcm),
                _fmt(storage_bcm),
                _fmt(dam.get('outflow')),
                _fmt(dam.get('outflow')),
                _fmt(dam.get('generation_mwh')),
                _fmt(dam.get('generation_mwh')),
                _fmt(fill_pct),
                _fmt(fill_pct),
            ]
        )
    return {
        'KPIs': kpis,
        'MonthSummary': summary,
        'Dams': dams,
        'Insights': _insights_rows(payload),
    }


def _drinking_water_sheets() -> dict[str, list[list[Any]]]:
    payload = build_drinking_water_dashboard_payload()
    kpis = _kpi_sheet('مؤشرات مياه الشرب', payload)
    meta: list[list[Any]] = [
        ['ملخص', 'Summary'],
        ['إجمالي المحطات', 'Stations total', payload.get('data_total')],
        ['المحافظة', 'Governorate', payload.get('selected_governorate') or '—'],
        ['سنة التسجيل', 'Enrollment year', payload.get('selected_enrollment_year') or '—'],
    ]
    return {
        'KPIs': kpis,
        'Summary': meta,
        'Insights': _insights_rows(payload),
    }


def build_water_section_export_sheets(
    section: str,
    *,
    year: int | None = None,
    month: str | None = None,
    basin: str | None = None,
    governorate: str | None = None,
) -> tuple[dict[str, list[list[Any]]], str]:
    key = (section or '').strip().lower()
    if key not in WATER_EXPORT_SECTIONS:
        raise detail_error('section must be rainfall, dams, euphrates, or drinking-water.')
    if key == 'rainfall':
        sheets = _rainfall_sheets(year=year, basin=basin, governorate=governorate)
        label = str(year or 'latest')
        return sheets, f'water_rainfall_report_{label}'
    if key == 'dams':
        sheets = _dams_sheets(year=year, governorate=governorate)
        label = str(year or 'latest')
        return sheets, f'water_dams_report_{label}'
    if key == 'euphrates':
        sheets = _euphrates_sheets(month=month)
        label = str(month or 'latest').replace('/', '-')
        return sheets, f'water_euphrates_report_{label}'
    sheets = _drinking_water_sheets()
    return sheets, 'water_drinking_water_report'


def export_water_dashboard_xlsx(
    *,
    section: str,
    year: int | None = None,
    month: str | None = None,
    basin: str | None = None,
    governorate: str | None = None,
) -> HttpResponse:
    sheets, stem = build_water_section_export_sheets(
        section, year=year, month=month, basin=basin, governorate=governorate,
    )
    return multisheet_xlsx_response(f'{stem}.xlsx', sheets)
