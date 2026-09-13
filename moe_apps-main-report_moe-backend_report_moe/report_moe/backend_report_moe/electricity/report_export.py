from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from water.template_generator import multisheet_xlsx_response, write_multisheet_xlsx_file

from .report_template import (
    CODE_TO_GOVERNORATE_AR,
    EXPORT_SHEET_ORDER,
    FUEL_MOVEMENT_EXPORT_ROWS,
    GENERATION_REPORT_EXPORT_ROWS,
    GENERATION_STATUS_EXPORT_ROWS,
    GENERATION_UNIT_EXPORT_ROWS,
    GOVERNORATE_EXPORT_ORDER,
    HYDRO_EXPORT_DAMS,
    LEGACY_SHEET_GENERATION_INCIDENTS,
    LEGACY_SHEET_GRID_INCIDENTS,
    METRIC_TO_EXTRACT_KEY,
    SHEET_FUEL_MOVEMENT,
    SHEET_FUEL_TANKS,
    SHEET_GENERATION_REPORT,
    SHEET_GENERATION_STATUS,
    SHEET_GENERATION_UNITS,
    SHEET_HYDRO,
    SHEET_MAINTENANCE,
    SHEET_REPORT_INFO,
)


def _parse_maintenance_groups(text: str) -> list[str]:
    return [line.strip() for line in (text or '').splitlines() if line.strip()]


def _metric_value(payload: dict[str, Any], metric_key: str) -> Any:
    for row in payload.get('metrics') or []:
        if row.get('metric_key') == metric_key and not row.get('dimension'):
            return row.get('value')
    return None


def _extract_row_value(row: dict[str, Any], metric_key: str) -> Any:
    extract_key = METRIC_TO_EXTRACT_KEY.get(metric_key, metric_key)
    value = row.get(extract_key)
    if value is not None:
        return value
    if metric_key == 'fuel_flow_consumed_tpd' and row.get('fuel_oil_consumed_t') is not None:
        return row.get('fuel_oil_consumed_t')
    if metric_key == 'fuel_oil_consumed_tpd':
        value = row.get('generation_status_fuel_oil_consumed_t')
        if value is not None:
            return value
        return row.get('fuel_oil_consumed_t')
    return None


def _report_value(source: dict[str, Any], metric_key: str) -> Any:
    if 'metrics' in source and isinstance(source.get('metrics'), list):
        return _metric_value(source, metric_key)
    return _extract_row_value(source, metric_key)


def _format_template_value(metric_key: str, value: Any) -> Any:
    if value is None:
        return None
    if metric_key == 'grid_frequency_hz':
        text = str(value).replace('.', ',')
        return text
    if metric_key == 'gas_import_mm3d' and isinstance(value, (int, float)):
        text = f'{value:.3f}'.replace('.', ',')
        return text
    return value


def _label_value_rows(
    source: dict[str, Any],
    rows: tuple[tuple[str, str], ...],
) -> list[list[Any]]:
    sheet_rows: list[list[Any]] = []
    for metric_key, label in rows:
        value = _format_template_value(
            metric_key, _report_value(source, metric_key))
        sheet_rows.append([label, value])
    return sheet_rows


def _coordinator_name(source: dict[str, Any]) -> str:
    notes = source.get('notes_ar') or ''
    return notes.replace('مدير التنسيق: ', '').strip()


def _report_date_label(source: dict[str, Any]) -> str:
    raw = source.get('report_date')
    if isinstance(raw, date):
        parsed = raw
    elif isinstance(raw, str):
        parsed = date.fromisoformat(raw)
    else:
        return ''
    return parsed.strftime('%d-%m-%Y')


def _governorate_loads_by_code(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    loads: dict[str, dict[str, Any]] = {}
    for item in source.get('governorate_loads') or []:
        code = item.get('governorate_code')
        if code:
            loads[code] = item
    return loads


def _build_report_info(source: dict[str, Any]) -> list[list[Any]]:
    return [
        ['التاريخ', _report_date_label(source)],
        ['مدير التنسيق', _coordinator_name(source)],
    ]


def _build_fuel_tanks_sheet(source: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [
        ['السعة الأعظمية (طن)', _report_value(
            source, 'fuel_tank_max_capacity_tons'), None, None],
        ['المخزون القابل للاستهلاك (طن)', _report_value(
            source, 'fuel_reserve_tons'), None, None],
        [
            'التردد (هيرتز)',
            _format_template_value('grid_frequency_hz',
                                   _report_value(source, 'grid_frequency_hz')),
            None,
            None,
        ],
        ['  مخزون خزانات الوقود (طن)', _report_value(
            source, 'fuel_tank_stock_tons'), None, None],
        [None, None, None, None],
        [None, None, None, None],
        ['استهلاك المحافظات', None, None, None],
        ['المحافظة', 'الكمية المستهلكة', 'الكمية المخصصة', 'التجاوز'],
    ]

    loads = _governorate_loads_by_code(source)
    for code in GOVERNORATE_EXPORT_ORDER:
        item = loads.get(code, {})
        consumed = item.get('consumed_mw')
        allocated = item.get('allocated_mw')
        excess = None
        if consumed is not None and allocated is not None:
            excess = allocated - consumed
        rows.append(
            [
                CODE_TO_GOVERNORATE_AR.get(code, code),
                consumed,
                allocated,
                excess,
            ],
        )

    rows.append(
        [
            'المجموع',
            _report_value(source, 'gov_consumed_mw'),
            _report_value(source, 'gov_allocated_mw'),
            _report_value(source, 'gov_excess_mw'),
        ],
    )
    return rows


def _generation_units_by_plant(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_plant: dict[str, dict[str, Any]] = {}
    for item in source.get('generation_unit_readings') or []:
        plant_code = item.get('plant_code')
        if plant_code:
            by_plant[plant_code] = item

    for item in source.get('hydro_readings') or []:
        dam_code = item.get('dam_code')
        if dam_code == 'euphrates':
            by_plant.setdefault(
                'euphrates_dam',
                {
                    'generation_mwh_24h': item.get('generation_mwh'),
                    'available_mw': None,
                },
            )
        elif dam_code == 'tishreen':
            by_plant.setdefault(
                'tishreen_dam',
                {
                    'generation_mwh_24h': item.get('generation_mwh'),
                    'available_mw': None,
                },
            )
    return by_plant


def _build_generation_units_sheet(source: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [
        [
            'المجموعة',
            'الانتاج',
            'استهلاك الوقود',
            ' الاستطاعة المتاحة (م.و) عند الساعة 9 ',
        ],
    ]
    by_plant = _generation_units_by_plant(source)
    for label, plant_code in GENERATION_UNIT_EXPORT_ROWS:
        if plant_code == 'tishreen_transformer':
            rows.append([label, 0, 0, 0])
            continue
        item = by_plant.get(plant_code, {})
        production = item.get('generation_mwh_24h')
        available = item.get('available_mw')
        rows.append(
            [
                label,
                0 if production is None else production,
                0,
                0 if available is None else available,
            ],
        )
    return rows


def _hydro_readings_by_code(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    readings: dict[str, dict[str, Any]] = {}
    for item in source.get('hydro_readings') or []:
        code = item.get('dam_code')
        if code:
            readings[code] = item
    return readings


def _build_hydro_sheet(source: dict[str, Any]) -> list[list[Any]]:
    readings = _hydro_readings_by_code(source)
    header = ['قيم/السد', *[label for label, _ in HYDRO_EXPORT_DAMS]]
    rows: list[list[Any]] = [header]
    field_rows = (
        ('front_level_m', ' المنسوب الامامي (م)'),
        ('back_level_m', 'المنسوب الخلفي (م)'),
        ('generation_mwh', 'الاستطاعه المولدة (م.و.س)'),
        ('outflow_m3s', 'المرر (م3 / ثا)'),
        ('inflow_m3s', 'الوارد (م3 / ثا)'),
        ('expected_m3s', 'المتوقع (م3 / ثا)'),
    )
    for field, label in field_rows:
        line = [label]
        for _, code in HYDRO_EXPORT_DAMS:
            line.append(readings.get(code, {}).get(field))
        rows.append(line)
    return rows


def _build_maintenance_sheet(source: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    maintenance_text = source.get('maintenance_groups_ar') or ''
    for label in _parse_maintenance_groups(maintenance_text):
        rows.append([label])
    return rows


def _build_generation_incidents_sheet(source: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [['الوقت', 'الوصف']]
    for item in source.get('generation_incidents') or []:
        rows.append([item.get('event_time'), item.get('description_ar')])
    return rows


def _build_grid_incidents_sheet(source: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [['الوقت', 'الإجراء']]
    for item in source.get('grid_incidents') or []:
        rows.append([item.get('event_time') or item.get(
            'line_name'), item.get('action_ar')])
    return rows


def build_electricity_report_sheets_from_source(source: dict[str, Any]) -> dict[str, list[list[Any]]]:
    """Build master-template workbook sheets from a DB payload or pdf_extract row dict."""
    sheets = {
        SHEET_REPORT_INFO: _build_report_info(source),
        SHEET_GENERATION_STATUS: _label_value_rows(source, GENERATION_STATUS_EXPORT_ROWS),
        SHEET_FUEL_MOVEMENT: _label_value_rows(source, FUEL_MOVEMENT_EXPORT_ROWS),
        SHEET_FUEL_TANKS: _build_fuel_tanks_sheet(source),
        SHEET_GENERATION_UNITS: _build_generation_units_sheet(source),
        SHEET_HYDRO: _build_hydro_sheet(source),
        SHEET_GENERATION_REPORT: _label_value_rows(source, GENERATION_REPORT_EXPORT_ROWS),
        SHEET_MAINTENANCE: _build_maintenance_sheet(source),
        LEGACY_SHEET_GRID_INCIDENTS: _build_grid_incidents_sheet(source),
        LEGACY_SHEET_GENERATION_INCIDENTS: _build_generation_incidents_sheet(source),
    }
    return {name: sheets[name] for name in EXPORT_SHEET_ORDER if name in sheets}


def build_electricity_report_sheets(report_date: date) -> dict[str, list[list[Any]]] | None:
    from .info_dashboard import build_info_report_detail_payload

    payload = build_info_report_detail_payload(report_date)
    if not payload:
        return None
    return build_electricity_report_sheets_from_source(payload)


def write_electricity_report_xlsx(source: dict[str, Any], path: Path) -> None:
    """Write a master-template XLSX file (report_01-05-2026 layout)."""
    sheets = build_electricity_report_sheets_from_source(source)
    write_multisheet_xlsx_file(path, sheets)


def export_electricity_report_xlsx(report_date: date):
    sheets = build_electricity_report_sheets(report_date)
    if not sheets:
        return None
    filename = f'report_{report_date.strftime("%d-%m-%Y")}.xlsx'
    return multisheet_xlsx_response(filename, sheets)
