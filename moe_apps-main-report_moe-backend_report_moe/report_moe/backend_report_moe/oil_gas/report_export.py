from __future__ import annotations

from datetime import date
from typing import Any

from water.template_generator import multisheet_xlsx_response

from .info_dashboard import build_info_dashboard_payload
from .report_template import (
    EXPORT_SHEET_ORDER,
    FIELDS_HEADER,
    METRICS_HEADER,
    REFINERIES_HEADER,
    SHEET_FIELDS,
    SHEET_METRICS,
    SHEET_REFINERIES,
    SHEET_SUMMARY,
    SUMMARY_DATE_LABEL,
    SUMMARY_STATUS_LABEL,
)


def build_oil_gas_report_sheets(report_date: date) -> dict[str, list[list[Any]]] | None:
    """Daily report export sheets, sourced from accepted Info (not legacy DailyReport)."""
    payload = build_info_dashboard_payload(report_date)
    if not payload or payload.get('status') != 'ready':
        return None

    summary = [
        [SUMMARY_DATE_LABEL, payload.get('report_date')],
        [SUMMARY_STATUS_LABEL, payload.get('status')],
    ]

    metrics = [
        list(METRICS_HEADER),
        *[
            [
                kpi.get('label_ar') or kpi.get('id'),
                kpi.get('label_en') or kpi.get('id'),
                kpi.get('value'),
                kpi.get('unit') or '',
            ]
            for kpi in payload.get('kpis') or []
        ],
    ]

    fields = [
        list(FIELDS_HEADER),
        *[
            [
                row.get('name_ar') or row.get('name_en') or row.get('code'),
                row.get('name_en'),
                row.get('crude_oil_bbl'),
                row.get('natural_gas_mmscf'),
                row.get('condensate_bbl'),
            ]
            for row in payload.get('fields') or []
        ],
    ]

    refineries = [
        list(REFINERIES_HEADER),
        *[
            [
                row.get('name_ar') or row.get('name_en'),
                row.get('name_en'),
                row.get('gasoline_ton'),
                row.get('diesel_ton'),
                row.get('fuel_oil_ton'),
                row.get('lpg_ton'),
            ]
            for row in payload.get('refineries') or []
        ],
    ]

    sheets = {
        SHEET_SUMMARY: summary,
        SHEET_METRICS: metrics,
        SHEET_FIELDS: fields,
        SHEET_REFINERIES: refineries,
    }
    return {name: sheets[name] for name in EXPORT_SHEET_ORDER if name in sheets}


def export_oil_gas_report_xlsx(report_date: date):
    sheets = build_oil_gas_report_sheets(report_date)
    if not sheets:
        return None
    filename = f'oil_gas_daily_report_{report_date.isoformat()}.xlsx'
    return multisheet_xlsx_response(filename, sheets)
