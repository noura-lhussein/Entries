"""Write electricity executive daily report spreadsheets (لوحة الكهرباء — نظرة تنفيذية)."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from openpyxl import Workbook

from .report_catalog import GENERATION_PLANT_BY_CODE

ARABIC_MONTH_BY_NUM: dict[int, str] = {
    1: 'كانون الثاني',
    2: 'شباط',
    3: 'آذار',
    4: 'نيسان',
    5: 'أيار',
    6: 'حزيران',
    7: 'تموز',
    8: 'آب',
    9: 'أيلول',
    10: 'تشرين الأول',
    11: 'تشرين الثاني',
    12: 'كانون الأخير',
}

GENERATION_BLOCK_LABELS: dict[str, str] = {
    'sweida': 'السويدية',
    'euphrates_dam': 'الفرات',
    'tishreen_dam': 'سد تشرين',
}

HYDRO_DAM_ORDER = ('thawra', 'euphrates', 'tishreen')
HYDRO_DAM_HEADERS = ('الفرات', 'تشرين')
HYDRO_FIELD_ROWS: tuple[tuple[str, str], ...] = (
    ('المنسوب الامامي', 'front_level_m'),
    ('المنسوب الخلفي', 'back_level_m'),
    ('الاستطاعه المولدة', 'generation_mwh'),
    ('المرر', 'outflow_m3s'),
    ('الوارد', 'inflow_m3s'),
    ('المتوقع', 'expected_m3s'),
)


def _format_report_date(value: str | date) -> str:
    if isinstance(value, str):
        parsed = date.fromisoformat(value)
    else:
        parsed = value
    month_name = ARABIC_MONTH_BY_NUM[parsed.month]
    return f'{parsed.year} {month_name} {parsed.day}'


def _cell_value(value: object) -> object:
    if value is None:
        return None
    return value


def _sum_fuel_tanks(row: dict, field: str) -> int | None:
    readings = row.get('fuel_tank_readings') or []
    if not readings:
        stock = row.get('fuel_tank_stock_tons')
        cap = row.get('fuel_tank_max_capacity_tons')
        if field == 'current_tons':
            return int(stock) if stock is not None else None
        if field == 'max_capacity_tons':
            return int(cap) if cap is not None else None
        return None
    total = 0
    found = False
    for item in readings:
        val = item.get(field)
        if val is not None:
            total += int(val)
            found = True
    return total if found else None


def _hydro_by_code(row: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for item in row.get('hydro_readings') or []:
        code = item.get('dam_code')
        if code:
            out[code] = item
    return out


def _generation_block(row: dict, plant_code: str) -> tuple[object, object]:
    for item in row.get('generation_unit_readings') or []:
        if item.get('plant_code') == plant_code:
            production = item.get('generation_mwh_24h')
            available = item.get('available_mw')
            return (_cell_value(production), _cell_value(available))
    return (None, None)


def _maintenance_labels(row: dict) -> list[str]:
    labels: list[str] = []
    for item in row.get('generation_unit_readings') or []:
        if item.get('status') == 'maintenance':
            code = item.get('unit_code') or item.get('plant_code') or ''
            if code and code != 'aggregate':
                labels.append(str(code))
            elif item.get('plant_code'):
                plant = GENERATION_PLANT_BY_CODE.get(item['plant_code'])
                labels.append(
                    plant.label_ar if plant else str(item['plant_code']))
    return labels


def _incidents_text(items: list[dict], key: str) -> str | None:
    parts: list[str] = []
    for item in items:
        text = (item.get(key) or '').strip().replace(
            '\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text)
        if text:
            parts.append(text)
    return '\n'.join(parts) if parts else None


def build_executive_rows(row: dict) -> list[list[object | None]]:
    """Map extract_pdf / extract_xlsx dict to sheet rows (label in A, value in B)."""
    fuel_stock = _sum_fuel_tanks(row, 'current_tons')
    fuel_max = _sum_fuel_tanks(row, 'max_capacity_tons')
    fuel_balance = row.get('fuel_oil_balance_t')
    if fuel_balance is None:
        received = row.get('fuel_oil_received_t')
        consumed = row.get('fuel_oil_consumed_t')
        if received is not None and consumed is not None:
            fuel_balance = received - consumed

    scalar_rows: list[tuple[str, object | None]] = [
        ('التاريخ', _format_report_date(row['report_date'])),
        ('ذروة التوليد', row.get('peak_mw')),
        ('التوليد الصافي', row.get('net_mwh_24h')),
        ('كمية الفيول المتاحة', row.get('available_fuel_quantity')),
        ('المخزون القابل', row.get('fuel_reserve_t')),
        ('معلومات خزانات الوقود (المخزون)', fuel_stock),
        ('السعة الأعظمية', fuel_max),
        ('كمية الفيول الواردة', row.get('fuel_oil_received_t')),
        ('حركة الفيول المستهلك', row.get('fuel_flow_consumed_tpd')),
        ('كمية الفيول المستهلكة', row.get('fuel_oil_consumed_t')),
        ('وفر الفيول', fuel_balance),
        ('الغاز الوارد', row.get('gas_import_mm3d')),
        ('الكمية المستهلكة اليومية من الغاز', row.get('gas_consumed_mm3d')),
        ('الطلب على الغاز', row.get('gas_demand_mm3d')),
        ('الاستطاعة المتاحة المولدة مع الشمسي',
         row.get('available_generated_power')),
        ('استطاعة المجموعات البخارية', row.get('steam_mwh')),
        ('مجموع التوليد البخاري على الفيول', row.get('steam_fuel_demand_tpd')),
        ('استطاعة المجموعات الغاز', row.get('gas_groups_mw')),
        ('استطاعة المجموعات البخار', row.get('steam_groups_mw')),
        ('استهلاك صناعي', row.get('industrial_mw')),
        ('استهلاك ذاتي', row.get('self_use_losses_mw')),
        ('الاستطاعة المولدة بدون صناعي', row.get(
            'generation_without_industrial_mw')),
        ('السدود', row.get('hydro_output_mw')),
        ('احتياط دوار', row.get('rotary_reserve_mw')),
        ('السدود المائية', row.get('hydro_dams_capacity_mw')),
        ('مجموع الاستطاعة الاسمية', row.get('nominal_capacity_mwh')),
        ('المجموع الكلي لانتاج', row.get('total_generation_mwh_24h')),
        ('مجموع التوليد الغازي', row.get('gas_generation_mwh_24h')),
        ('الطلب الكلي على الفيول', row.get('total_fuel_demand_tpd')),
        ('التردد', row.get('grid_frequency_hz')),
        ('الكمية المستجرة', row.get('gov_consumed_mw')),
        ('الكمية المخصصة', row.get('gov_allocated_mw')),
        ('التجاوز', row.get('gov_excess_mw')),
        ('عنفات شمسي', row.get('solar_capacity_mw')),
        ('عنفات ريحي', row.get('wind_capacity_mw')),
    ]

    rows: list[list[object | None]] = [
        [label, _cell_value(value)] for label, value in scalar_rows]

    hydro = _hydro_by_code(row)
    if hydro:
        rows.append(['معلومات', *HYDRO_DAM_HEADERS])
        for label, field in HYDRO_FIELD_ROWS:
            line: list[object | None] = [label]
            for code in HYDRO_DAM_ORDER:
                reading = hydro.get(code, {})
                line.append(_cell_value(reading.get(field)))
            rows.append(line)

    for plant_code, block_label in GENERATION_BLOCK_LABELS.items():
        production, available = _generation_block(row, plant_code)
        if production is not None or available is not None:
            rows.append([block_label, production, available])

    maintenance = _maintenance_labels(row)
    if maintenance:
        rows.append(['المجموعات تحت أعمال الصيانة', None])
        for label in maintenance:
            rows.append([label, None])

    gen_text = _incidents_text(
        row.get('generation_incidents') or [], 'description_ar')
    if gen_text:
        rows.append(['حوادث مجموعات التوليد', gen_text])

    grid_text = _incidents_text(row.get('grid_incidents') or [], 'line_name')
    if grid_text:
        rows.append(['حوادث الخطوط', grid_text])

    return rows


def write_executive_xlsx(row: dict, path: Path) -> None:
    """Write single-sheet executive workbook from an extracted report dict."""
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'لوحة الكهرباء'
    for row_index, sheet_row in enumerate(build_executive_rows(row), start=1):
        for col_index, value in enumerate(sheet_row, start=1):
            worksheet.cell(row=row_index, column=col_index, value=value)
    workbook.save(path)
