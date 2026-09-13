"""Excel export for geology ore production & contracts (read-only, from Info)."""

from __future__ import annotations

from datetime import date
from typing import Any

from django.http import HttpResponse
from water.template_generator import multisheet_xlsx_response

from .info_dashboard import build_ore_production_info_dashboard

SHEET_ORE = 'إنتاج الخامات'

ORE_HEADERS = [
    'المنتج',
    'Product (EN)',
    'النوع',
    'الوحدة',
    'المخطط السنوي',
    'مخطط النصف الأول',
    'المنفذ (النصف الأول)',
    'نسبة التنفيذ %',
    'عدد العقود',
    'الاحتياطي',
]


def _ore_row_to_sheet(row: dict[str, Any]) -> list[Any]:
    return [
        row.get('product_name_ar') or '',
        row.get('product_name_en') or '',
        row.get('production_type') or '',
        row.get('unit') or '',
        row.get('annual_plan_tons'),
        row.get('h1_plan_tons'),
        row.get('h1_executed_tons'),
        row.get('execution_pct'),
        row.get('contract_count'),
        row.get('reserve_text') or '',
    ]


def export_ore_production_xlsx(plan_year: int | None = None) -> HttpResponse | None:
    payload = build_ore_production_info_dashboard(plan_year=plan_year)
    if payload is None:
        return None
    year = int(payload.get('plan_year') or plan_year or date.today().year)
    sheet = [ORE_HEADERS]
    sheet.extend(_ore_row_to_sheet(row) for row in payload.get('rows') or [])
    filename = f'geology_ore_production_{year}.xlsx'
    return multisheet_xlsx_response(filename, {SHEET_ORE: sheet})
