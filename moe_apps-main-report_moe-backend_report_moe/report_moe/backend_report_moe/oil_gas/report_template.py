"""Official oil & gas daily workbook sheet names and blank template rows.

Shape matches ``scripts/oil_gas_daily_report_*.xlsx`` /
``build_oil_gas_report_sheets`` (ملخص + المؤشرات + الحقول + المصافي).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .metric_catalog import EXECUTIVE_METRIC_SPECS, resolve_metric_labels

SHEET_SUMMARY = "ملخص"
SHEET_METRICS = "المؤشرات"
SHEET_FIELDS = "الحقول"
SHEET_REFINERIES = "المصافي"

EXPORT_SHEET_ORDER: tuple[str, ...] = (
    SHEET_SUMMARY,
    SHEET_METRICS,
    SHEET_FIELDS,
    SHEET_REFINERIES,
)

SUMMARY_DATE_LABEL = "تاريخ التقرير / Report date"
SUMMARY_STATUS_LABEL = "الحالة / Status"
SUMMARY_NOTES_AR_LABEL = "ملاحظات (ع)"
SUMMARY_NOTES_EN_LABEL = "Notes (en)"

METRICS_HEADER = ["المؤشر", "Metric", "القيمة", "الوحدة"]
FIELDS_HEADER = [
    "الحقل",
    "Field",
    "إنتاج النفط الخام (برميل)",
    "إنتاج الغاز (مليون قدم مكعب)",
    "المكثفات (برميل)",
]
REFINERIES_HEADER = [
    "المصفاة",
    "Refinery",
    "البنزين (طن)",
    "المازوت (طن)",
    "زيت الوقود (طن)",
    "الغاز المسال (طن)",
]


def build_oil_gas_blank_template_sheets(
    sample_date: date | None = None,
) -> dict[str, list[list[Any]]]:
    report_date = sample_date or date.today()
    summary = [
        [SUMMARY_DATE_LABEL, report_date.isoformat()],
        [SUMMARY_STATUS_LABEL, ""],
        [SUMMARY_NOTES_AR_LABEL, ""],
        [SUMMARY_NOTES_EN_LABEL, ""],
    ]
    metrics: list[list[Any]] = [list(METRICS_HEADER)]
    for spec in EXECUTIVE_METRIC_SPECS:
        label_en, label_ar = resolve_metric_labels(spec, report_date)
        metrics.append([label_ar, label_en, None, spec.unit])
    return {
        SHEET_SUMMARY: summary,
        SHEET_METRICS: metrics,
        SHEET_FIELDS: [list(FIELDS_HEADER)],
        SHEET_REFINERIES: [list(REFINERIES_HEADER)],
    }
