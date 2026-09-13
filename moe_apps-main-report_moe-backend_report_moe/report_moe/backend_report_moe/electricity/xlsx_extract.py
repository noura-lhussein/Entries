"""Parse electricity daily report spreadsheets (multi-sheet master workbook or legacy single sheet)."""
from __future__ import annotations

import re
from datetime import date, time
from pathlib import Path

from openpyxl import load_workbook

from .report_catalog import NATIONAL_FUEL_RESERVE_CAPACITY_TONS
from .report_template import (
    GENERATION_GROUP_AR_TO_PLANT,
    GOVERNORATE_AR_TO_CODE,
    HYDRO_DAM_AR_TO_CODE,
    LEGACY_SHEET_GENERATION_INCIDENTS,
    LEGACY_SHEET_GRID_INCIDENTS,
    SHEET_FUEL_MOVEMENT,
    SHEET_FUEL_TANKS,
    SHEET_GENERATION_INCIDENTS,
    SHEET_GENERATION_REPORT,
    SHEET_GENERATION_STATUS,
    SHEET_GENERATION_UNITS,
    SHEET_GRID_INCIDENTS,
    SHEET_HYDRO,
    SHEET_MAINTENANCE,
    SHEET_REPORT_INFO,
)

ARABIC_MONTHS = {
    'كانون الثاني': 1,
    'كانون الاول': 1,
    'كانون الأول': 1,
    'شباط': 2,
    'آذار': 3,
    'اذار': 3,
    'نيسان': 4,
    'أيار': 5,
    'ايار': 5,
    'حزيران': 6,
    'تموز': 7,
    'آب': 8,
    'اب': 8,
    'أيلول': 9,
    'ايلول': 9,
    'تشرين الأول': 10,
    'تشرين الاول': 10,
    'تشرين الثاني': 11,
    'كانون الثاني ': 12,
    'كانون الاخير': 12,
    'كانون الأخير': 12,
}


def _normalize_label(value: object) -> str:
    if value is None:
        return ''
    text = str(value).strip().replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text)


def _parse_num(value: object) -> float | None:
    if value is None or value == '':
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(',', '.').replace('٫', '.')
    text = re.sub(r'[^\d.\-]', '', text)
    if not text or text in {'-', '.'}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _scale_thousands_tons(value: float | None) -> float | None:
    if value is None:
        return None
    if value < 1000:
        return round(value * 1000, 3)
    return value


def parse_report_date_from_text(value: object) -> date | None:
    text = _normalize_label(value)
    if not text:
        return None
    match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', text)
    if match:
        day, month, year = (int(match.group(1)), int(
            match.group(2)), int(match.group(3)))
        try:
            return date(year, month, day)
        except ValueError:
            return None
    match = re.search(r'(\d{4})\s+([^\d]+?)\s+(\d{1,2})', text)
    if not match:
        return None
    year = int(match.group(1))
    month_name = match.group(2).strip()
    day = int(match.group(3))
    month = ARABIC_MONTHS.get(month_name)
    if month is None:
        for key, month_num in ARABIC_MONTHS.items():
            if key in month_name or month_name in key:
                month = month_num
                break
    if month is None:
        return None
    return date(year, month, day)


def _sheet_rows(workbook, sheet_name: str) -> list[list[object | None]]:
    worksheet = workbook[sheet_name]
    return [list(row) for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, values_only=True)]


def _rows_from_workbook(path: Path) -> list[list[object | None]]:
    workbook = load_workbook(path, data_only=True)
    worksheet = workbook.active
    return [list(row) for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, values_only=True)]


def _row_label(row: list[object | None]) -> str:
    return _normalize_label(row[0] if row else '')


def _find_row(rows: list[list[object | None]], pattern: str) -> list[object | None] | None:
    for row in rows:
        if re.search(pattern, _row_label(row)):
            return row
    return None


def _metric(rows: list[list[object | None]], pattern: str) -> float | None:
    row = _find_row(rows, pattern)
    if not row:
        return None
    return _parse_num(row[1] if len(row) > 1 else None)


def _kv_metrics(rows: list[list[object | None]], patterns: dict[str, str]) -> dict[str, float | None]:
    return {key: _metric(rows, pattern) for key, pattern in patterns.items()}


def _is_multisheet_workbook(path: Path) -> bool:
    workbook = load_workbook(path, read_only=True, data_only=True)
    names = set(workbook.sheetnames)
    workbook.close()
    return SHEET_REPORT_INFO in names or SHEET_GENERATION_STATUS in names


def _parse_report_info(rows: list[list[object | None]]) -> tuple[date | None, str]:
    report_date = None
    coordinator = ''
    for row in rows:
        label = _row_label(row)
        if label == 'التاريخ' and len(row) > 1:
            report_date = parse_report_date_from_text(row[1])
        elif 'مدير التنسيق' in label and len(row) > 1:
            coordinator = _normalize_label(row[1])
    return report_date, coordinator


def _parse_governorate_table(rows: list[list[object | None]]) -> list[dict]:
    loads: list[dict] = []
    in_table = False
    for row in rows:
        label = _row_label(row)
        if label == 'المحافظة':
            in_table = True
            continue
        if not in_table or not label:
            continue
        code = GOVERNORATE_AR_TO_CODE.get(label)
        if not code or code == 'national_total':
            continue
        consumed = _parse_num(row[1] if len(row) > 1 else None)
        allocated = _parse_num(row[2] if len(row) > 2 else None)
        if consumed is None and allocated is None:
            continue
        loads.append(
            {
                'governorate_code': code,
                'consumed_mw': consumed,
                'allocated_mw': allocated,
            },
        )
    return loads


def _parse_generation_units_table(rows: list[list[object | None]]) -> list[dict]:
    units: list[dict] = []
    for row in rows[1:]:
        label = _row_label(row)
        if not label or label == 'المجموعة':
            continue
        plant_code = ''
        for pattern, code in GENERATION_GROUP_AR_TO_PLANT:
            if re.search(pattern, label):
                plant_code = code
                break
        if not plant_code:
            continue
        production = _parse_num(row[1] if len(row) > 1 else None)
        fuel_use = _parse_num(row[2] if len(row) > 2 else None)
        available = _parse_num(row[3] if len(row) > 3 else None)
        if production is None and available is None:
            continue
        units.append(
            {
                'plant_code': plant_code,
                'unit_code': label[:32],
                'generation_mwh_24h': production,
                'available_mw': available,
                'status': 'active' if (available or 0) > 0 or (production or 0) > 0 else 'standby',
                'fuel_consumed_tpd': fuel_use,
            },
        )
    return units


def _parse_hydro_table(rows: list[list[object | None]]) -> list[dict]:
    if not rows:
        return []
    header = rows[0]
    dam_codes: list[str] = []
    for col in header[1:]:
        label = _normalize_label(col)
        if not label:
            continue
        code = HYDRO_DAM_AR_TO_CODE.get(label)
        if code:
            dam_codes.append(code)
    if not dam_codes:
        return []

    readings = [{'dam_code': code} for code in dam_codes]
    field_map = {
        'المنسوب الامامي': 'front_level_m',
        'المنسوب الخلفي': 'back_level_m',
        'الاستطاعه المولدة': 'generation_mwh',
        'المرر': 'outflow_m3s',
        'الوارد': 'inflow_m3s',
        'المتوقع': 'expected_m3s',
    }
    for row in rows[1:]:
        label = _row_label(row)
        field = None
        for key, attr in field_map.items():
            if key in label:
                field = attr
                break
        if not field:
            continue
        for index, code in enumerate(dam_codes):
            value = _parse_num(row[index + 1] if len(row)
                               > index + 1 else None)
            if value is not None:
                readings[index][field] = value
    return [reading for reading in readings if len(reading) > 1]


def _parse_incident_table(
    rows: list[list[object | None]],
    *,
    kind: str,
) -> list[dict]:
    incidents: list[dict] = []
    for row in rows[1:]:
        event_time = _normalize_label(row[0] if row else '')
        detail = _normalize_label(row[1] if len(row) > 1 else '')
        if not event_time or not detail or event_time in {'الوقت', 'Time'}:
            continue
        if kind == 'generation':
            incidents.append(
                {'event_time': event_time, 'description_ar': detail, 'description_en': ''})
        else:
            incidents.append({'line_name': event_time, 'action_ar': detail,
                             'action_en': '', 'event_time': event_time})
    return incidents


def _parse_maintenance_text(rows: list[list[object | None]]) -> str:
    lines: list[str] = []
    for row in rows:
        label = _row_label(row)
        if not label or label in {'المجموعة', 'المجموعات تحت أعمال الصيانة'}:
            continue
        lines.append(label)
    return '\n'.join(lines)


def _sheet_rows_by_names(workbook, *names: str) -> list[list[object | None]]:
    for name in names:
        if name in workbook.sheetnames:
            return _sheet_rows(workbook, name)
    return []


def _extract_multisheet(path: Path) -> dict:
    workbook = load_workbook(path, data_only=True)
    sheets = {name: _sheet_rows(workbook, name)
              for name in workbook.sheetnames}

    report_date, coordinator = _parse_report_info(
        sheets.get(SHEET_REPORT_INFO, []))
    if report_date is None:
        workbook.close()
        raise ValueError(
            f'Could not parse report date from spreadsheet: {path.name}')

    status_metrics = _kv_metrics(
        sheets.get(SHEET_GENERATION_STATUS, []),
        {
            'nominal_capacity_mwh': r'مجموع الاستطاعة الاسمية',
            'total_generation_mwh_24h': r'المجموع الكلي لانتاج',
            'gas_generation_mwh_24h': r'مجموع التوليد الغازي',
            'steam_fuel_demand_tpd': r'مجموع التوليد البخاري على الفيول',
            'gas_demand_mm3d': r'الطلب على الغاز',
            'total_fuel_demand_tpd': r'الطلب الكلي على الفيول',
            'gas_consumed_mm3d': r'الكمية المستهلكة اليومية من الغاز',
            'fuel_oil_consumed_tpd': r'الكمية المستهلكة من الفيول',
            'hydro_dams_capacity_mw': r'للسدود|سدود.*المائي|الاستطاعة المتاحة.*سدود',
            'solar_capacity_mw': r'العنافات الشمسية|عنفات شمسي|الاستطاعة المتاحة.*الشمسية',
            'wind_capacity_mw': r'العنافات الريحية|عنفات ريحي|الاستطاعة المتاحة.*الريحية',
        },
    )

    fuel_movement = _kv_metrics(
        sheets.get(SHEET_FUEL_MOVEMENT, []),
        {
            'fuel_oil_received_tpd': r'الفيول الوارد',
            'fuel_flow_consumed_tpd': r'الفيول المستهلك',
            'fuel_oil_balance_tpd': r'وفر الفيول',
        },
    )

    fuel_tanks_rows = sheets.get(SHEET_FUEL_TANKS, [])
    fuel_tanks = _kv_metrics(
        fuel_tanks_rows,
        {
            'fuel_tank_max_capacity_tons': r'السعة الأعظمية',
            'fuel_reserve_tons': r'المخزون القابل للاستهلاك',
            'grid_frequency_hz': r'التردد',
            'fuel_tank_stock_tons': r'المخزون الكلي في بداية العام|بداية العام',
        },
    )
    if fuel_tanks['fuel_tank_stock_tons'] is None:
        fuel_tanks['fuel_tank_stock_tons'] = _metric(
            fuel_tanks_rows, r'بداية العام')

    generation_report = _kv_metrics(
        sheets.get(SHEET_GENERATION_REPORT, []),
        {
            'available_generated_power': r'الاستطاعة المتاحة المولدة مع الشمسي',
            'self_use_losses_mw': r'استهلاك ذاتي',
            'net_generation_mwh': r'التوليد الصافي',
            'industrial_self_use_mw': r'استهلاك صناعي',
            'generation_without_industrial_mw': r'الاستطاعة المولدة بدون صناعي',
            'hydro_output_mw': r'^السدود',
            'rotary_reserve_mw': r'احتياط دوار',
            'gov_consumed_mw': r'الاستطاعة المستهلكة',
            'gas_groups_mw': r'استطاعة المجموعات الغاز',
            'steam_groups_mw': r'استطاعة المجموعات البخار',
            'gas_import_mm3d': r'الغاز الوارد',
            'fuel_reserve_tons': r'المخزون الاحتياطي من الفيول|المخزون الاحتياطي',
        },
    )

    governorate_loads = _parse_governorate_table(fuel_tanks_rows)
    totals_row = _find_row(fuel_tanks_rows, r'^المجموع$')
    gov_consumed = _parse_num(
        totals_row[1] if totals_row and len(totals_row) > 1 else None)
    gov_allocated = _parse_num(
        totals_row[2] if totals_row and len(totals_row) > 2 else None)
    gov_excess = _parse_num(
        totals_row[3] if totals_row and len(totals_row) > 3 else None)
    if gov_consumed is None:
        gov_consumed = generation_report.get('gov_consumed_mw')

    generation_units = _parse_generation_units_table(
        sheets.get(SHEET_GENERATION_UNITS, []))
    maintenance_groups_ar = _parse_maintenance_text(
        sheets.get(SHEET_MAINTENANCE, []))
    hydro_readings = _parse_hydro_table(sheets.get(SHEET_HYDRO, []))

    generation_incidents = _parse_incident_table(
        _sheet_rows_by_names(
            workbook,
            SHEET_GENERATION_INCIDENTS,
            LEGACY_SHEET_GENERATION_INCIDENTS,
        ),
        kind='generation',
    )
    grid_incidents = _parse_incident_table(
        _sheet_rows_by_names(
            workbook,
            SHEET_GRID_INCIDENTS,
            LEGACY_SHEET_GRID_INCIDENTS,
        ),
        kind='grid',
    )

    workbook.close()

    fuel_reserve = fuel_tanks.get('fuel_reserve_tons')
    if fuel_reserve is None:
        fuel_reserve = generation_report.get('fuel_reserve_tons')
    fuel_max = fuel_tanks.get('fuel_tank_max_capacity_tons')
    fuel_balance = fuel_movement.get('fuel_oil_balance_tpd')
    fuel_received = fuel_movement.get('fuel_oil_received_tpd')
    fuel_consumed = fuel_movement.get('fuel_flow_consumed_tpd')
    if fuel_balance is None and fuel_received is not None and fuel_consumed is not None:
        fuel_balance = fuel_received - fuel_consumed

    notes_ar = f'مدير التنسيق: {coordinator}' if coordinator else ''

    row = {
        'report_date': report_date.isoformat(),
        'source_file': path.name,
        'reference_hour': time(9, 0),
        'peak_generation_time': None,
        'notes_ar': notes_ar,
        'maintenance_groups_ar': maintenance_groups_ar,
        'peak_mw': None,
        'net_mwh_24h': generation_report.get('net_generation_mwh'),
        'available_fuel_quantity': None,
        'fuel_reserve_t': int(fuel_reserve) if fuel_reserve is not None else None,
        'fuel_tank_stock_tons': int(fuel_tanks['fuel_tank_stock_tons']) if fuel_tanks.get('fuel_tank_stock_tons') is not None else None,
        'fuel_tank_max_capacity_tons': int(fuel_max) if fuel_max is not None else None,
        'fuel_oil_received_t': int(fuel_received) if fuel_received is not None else None,
        'fuel_flow_consumed_tpd': int(fuel_consumed) if fuel_consumed is not None else None,
        'fuel_oil_consumed_t': int(fuel_consumed) if fuel_consumed is not None else None,
        'generation_status_fuel_oil_consumed_t': (
            int(status_metrics['fuel_oil_consumed_tpd'])
            if status_metrics.get('fuel_oil_consumed_tpd') is not None else None
        ),
        'fuel_oil_balance_t': int(fuel_balance) if fuel_balance is not None else None,
        'gas_import_mm3d': generation_report.get('gas_import_mm3d') or status_metrics.get('gas_consumed_mm3d'),
        'gas_consumed_mm3d': status_metrics.get('gas_consumed_mm3d'),
        'gas_demand_mm3d': status_metrics.get('gas_demand_mm3d'),
        'available_generated_power': generation_report.get('available_generated_power'),
        'steam_mwh': generation_report.get('steam_groups_mw'),
        'steam_fuel_demand_tpd': status_metrics.get('steam_fuel_demand_tpd'),
        'gas_groups_mw': generation_report.get('gas_groups_mw'),
        'steam_groups_mw': generation_report.get('steam_groups_mw'),
        'industrial_mw': generation_report.get('industrial_self_use_mw'),
        'self_use_losses_mw': generation_report.get('self_use_losses_mw'),
        'generation_without_industrial_mw': generation_report.get('generation_without_industrial_mw'),
        'hydro_output_mw': generation_report.get('hydro_output_mw'),
        'rotary_reserve_mw': generation_report.get('rotary_reserve_mw'),
        'hydro_dams_capacity_mw': status_metrics.get('hydro_dams_capacity_mw'),
        'nominal_capacity_mwh': status_metrics.get('nominal_capacity_mwh'),
        'total_generation_mwh_24h': status_metrics.get('total_generation_mwh_24h'),
        'gas_generation_mwh_24h': status_metrics.get('gas_generation_mwh_24h'),
        'total_fuel_demand_tpd': status_metrics.get('total_fuel_demand_tpd'),
        'grid_frequency_hz': fuel_tanks.get('grid_frequency_hz'),
        'gov_consumed_mw': gov_consumed,
        'gov_allocated_mw': gov_allocated,
        'gov_excess_mw': gov_excess,
        'solar_capacity_mw': status_metrics.get('solar_capacity_mw'),
        'wind_capacity_mw': status_metrics.get('wind_capacity_mw'),
        'generation_incidents_count': len(generation_incidents),
        'grid_incidents_count': len(grid_incidents),
        'governorate_loads': governorate_loads,
        'hydro_readings': hydro_readings,
        'fuel_tank_readings': [],
        'generation_unit_readings': generation_units,
        'generation_incidents': generation_incidents,
        'grid_incidents': grid_incidents,
    }

    if row['fuel_reserve_t']:
        capacity = row['fuel_tank_max_capacity_tons'] or NATIONAL_FUEL_RESERVE_CAPACITY_TONS
        row['fuel_reserve_pct'] = round(
            row['fuel_reserve_t'] / capacity * 100, 1)

    return row


def _split_incidents(text: str) -> list[str]:
    raw = str(text).strip() if text is not None else ''
    if not raw:
        return []
    if '\n' in raw:
        return [part.strip() for part in raw.splitlines() if part.strip()]
    normalized = _normalize_label(raw)
    if '|' in normalized:
        parts = re.split(r'\s*\|\s*', normalized)
        return [part.strip() for part in parts if part.strip()]
    if re.search(r'\s[-–—]\s', normalized) and normalized.count(' - ') + normalized.count(' – ') + normalized.count(' — ') >= 2:
        parts = re.split(r'\s*[-–—]\s*', normalized)
        return [part.strip() for part in parts if part.strip()]
    return [normalized]


def _parse_maintenance_text_legacy(rows: list[list[object | None]]) -> str:
    lines: list[str] = []
    in_section = False
    for row in rows:
        label = _row_label(row)
        if 'المجموعات تحت أعمال الصيانة' in label:
            in_section = True
            continue
        if not in_section:
            continue
        if 'حوادث الشبكة' in label or 'حوادث الخطوط' in label:
            break
        if not label or _parse_num(row[1] if len(row) > 1 else None) is not None:
            continue
        lines.append(label)
    return '\n'.join(lines)


def _parse_generation_unit_blocks(rows: list[list[object | None]]) -> list[dict]:
    units: list[dict] = []
    patterns = [
        ('sweida', r'السويدية'),
        ('euphrates_dam', r'الفرات|كديران'),
        ('tishreen_dam', r'سد تشرين'),
    ]
    for plant_code, pattern in patterns:
        row = _find_row(rows, pattern)
        if not row:
            continue
        production = _parse_num(row[1] if len(row) > 1 else None)
        available = _parse_num(row[2] if len(row) > 2 else None)
        if production is None and available is None:
            continue
        units.append(
            {
                'plant_code': plant_code,
                'unit_code': 'aggregate',
                'generation_mwh_24h': production,
                'available_mw': available,
                'status': 'active',
            },
        )
    return units


def _parse_hydro_table_legacy(rows: list[list[object | None]]) -> list[dict]:
    header_index = None
    for index, row in enumerate(rows):
        label = _row_label(row)
        if label == 'معلومات' and len(row) > 3 and 'الفرات' in _normalize_label(row[2]):
            header_index = index
            break
    if header_index is None:
        return []

    dam_codes = ['thawra', 'euphrates', 'tishreen']
    readings = [{'dam_code': code} for code in dam_codes]
    field_map = {
        'المنسوب الامامي': 'front_level_m',
        'المنسوب الخلفي': 'back_level_m',
        'الاستطاعه المولدة': 'generation_mwh',
        'المرر': 'outflow_m3s',
        'الوارد': 'inflow_m3s',
        'المتوقع': 'expected_m3s',
    }
    for row in rows[header_index + 1: header_index + 8]:
        label = _row_label(row)
        field = field_map.get(label)
        if not field:
            continue
        for index, code in enumerate(dam_codes):
            value = _parse_num(row[index + 1] if len(row)
                               > index + 1 else None)
            if value is not None:
                readings[index][field] = value
    return [reading for reading in readings if len(reading) > 1]


def _extract_legacy(path: Path) -> dict:
    rows = _rows_from_workbook(path)
    date_row = _find_row(rows, r'^التاريخ$')
    report_date = None
    if date_row and len(date_row) > 1:
        report_date = parse_report_date_from_text(date_row[1])
    if report_date is None:
        raise ValueError(
            f'Could not parse report date from spreadsheet: {path.name}')

    fuel_reserve = _scale_thousands_tons(_metric(rows, r'المخزون القابل'))
    if fuel_reserve is None:
        fuel_reserve = _scale_thousands_tons(
            _metric(rows, r'المخزون الاحتياطي'))
    fuel_stock = _scale_thousands_tons(
        _metric(rows, r'معلومات خزانات الوقود \(المخزون\)'))
    fuel_max = _scale_thousands_tons(_metric(rows, r'السعة الأعظمية'))

    fuel_received = _metric(rows, r'حركة الفيول الوارد|كمية الفيول الواردة')
    fuel_flow_consumed = _metric(rows, r'حركة الفيول المستهلك')
    fuel_consumed = _metric(
        rows, r'الكمية المستهلكة من الفيول|كمية الفيول المستهلكة')
    fuel_balance = _metric(rows, r'وفر الفيول')
    if fuel_balance is None and fuel_received is not None and fuel_consumed is not None:
        fuel_balance = fuel_received - fuel_consumed

    gas_import = _metric(rows, r'الغاز الوارد')
    gas_consumed = _metric(rows, r'الكمية المستهلكة اليومية من الغاز')
    gas_demand = _metric(rows, r'الطلب على الغاز')

    gen_incidents_row = _find_row(rows, r'حوادث مجموعات التوليد')
    grid_incidents_row = _find_row(rows, r'^حوادث الخطوط$')

    generation_incidents: list[dict] = []
    if gen_incidents_row and len(gen_incidents_row) > 1 and gen_incidents_row[1] is not None:
        for part in _split_incidents(str(gen_incidents_row[1])):
            generation_incidents.append(
                {'description_ar': part, 'description_en': ''})

    grid_incidents: list[dict] = []
    if grid_incidents_row and len(grid_incidents_row) > 1 and grid_incidents_row[1] is not None:
        for part in _split_incidents(str(grid_incidents_row[1])):
            grid_incidents.append(
                {'line_name': part, 'action_ar': part, 'action_en': ''})

    maintenance_groups_ar = _parse_maintenance_text_legacy(rows)
    generation_units = _parse_generation_unit_blocks(rows)
    hydro_readings = _parse_hydro_table_legacy(rows)

    row = {
        'report_date': report_date.isoformat(),
        'source_file': path.name,
        'reference_hour': time(9, 0),
        'peak_generation_time': None,
        'notes_ar': '',
        'maintenance_groups_ar': maintenance_groups_ar,
        'peak_mw': _metric(rows, r'ذروة التوليد'),
        'net_mwh_24h': _metric(rows, r'التوليد الصافي'),
        'available_fuel_quantity': _metric(rows, r'كمية الفيول المتاحة'),
        'fuel_reserve_t': int(fuel_reserve) if fuel_reserve is not None else None,
        'fuel_tank_stock_tons': int(fuel_stock) if fuel_stock is not None else None,
        'fuel_tank_max_capacity_tons': int(fuel_max) if fuel_max is not None else None,
        'fuel_oil_received_t': int(fuel_received) if fuel_received is not None else None,
        'fuel_flow_consumed_tpd': int(fuel_flow_consumed) if fuel_flow_consumed is not None else None,
        'fuel_oil_consumed_t': int(fuel_consumed) if fuel_consumed is not None else None,
        'fuel_oil_balance_t': int(fuel_balance) if fuel_balance is not None else None,
        'gas_import_mm3d': gas_import,
        'gas_consumed_mm3d': gas_consumed,
        'gas_demand_mm3d': gas_demand,
        'available_generated_power': _metric(rows, r'الاستطاعة المتاحة المولدة مع الشمسي'),
        'steam_mwh': _metric(rows, r'^استطاعة المجموعات البخارية$'),
        'steam_fuel_demand_tpd': _metric(rows, r'مجموع التوليد البخاري على الفيول'),
        'gas_groups_mw': _metric(rows, r'استطاعة المجموعات الغاز'),
        'steam_groups_mw': _metric(rows, r'استطاعة المجموعات البخار'),
        'industrial_mw': _metric(rows, r'استهلاك صناعي'),
        'self_use_losses_mw': _metric(rows, r'استهلاك ذاتي'),
        'generation_without_industrial_mw': _metric(rows, r'الاستطاعة المولدة بدون صناعي'),
        'hydro_output_mw': _metric(rows, r'^السدود$'),
        'rotary_reserve_mw': _metric(rows, r'احتياط دوار'),
        'hydro_dams_capacity_mw': _metric(rows, r'للسدود|سدود.*المائي'),
        'nominal_capacity_mwh': _metric(rows, r'مجموع الاستطاعة الاسمية'),
        'total_generation_mwh_24h': _metric(rows, r'المجموع الكلي لانتاج'),
        'gas_generation_mwh_24h': _metric(rows, r'مجموع التوليد الغازي'),
        'total_fuel_demand_tpd': _metric(rows, r'الطلب الكلي على الفيول'),
        'grid_frequency_hz': _metric(rows, r'^التردد$'),
        'gov_consumed_mw': _metric(rows, r'الكمية المستجرة'),
        'gov_allocated_mw': _metric(rows, r'الكمية المخصصة'),
        'gov_excess_mw': _metric(rows, r'^التجاوز$'),
        'solar_capacity_mw': _metric(rows, r'العنافات الشمسية|عنفات شمسي'),
        'wind_capacity_mw': _metric(rows, r'العنافات الريحية|عنفات ريحي'),
        'generation_incidents_count': len(generation_incidents),
        'grid_incidents_count': len(grid_incidents),
        'governorate_loads': [],
        'hydro_readings': hydro_readings,
        'fuel_tank_readings': [],
        'generation_unit_readings': generation_units,
        'generation_incidents': generation_incidents,
        'grid_incidents': grid_incidents,
    }

    if row['fuel_reserve_t']:
        capacity = row['fuel_tank_max_capacity_tons'] or NATIONAL_FUEL_RESERVE_CAPACITY_TONS
        row['fuel_reserve_pct'] = round(
            row['fuel_reserve_t'] / capacity * 100, 1)

    return row


def extract_xlsx(path: Path) -> dict:
    if _is_multisheet_workbook(path):
        return _extract_multisheet(path)
    return _extract_legacy(path)
