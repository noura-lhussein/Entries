"""Generate electricity daily executive report PDF."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz
from config.pdf_arabic import ArabicPdfText, apply_rtl_document
from config.pdf_letterhead import draw_electricity_letterhead
from django.http import HttpResponse

from .info_dashboard import build_info_report_detail_payload
from .metric_catalog import METRIC_SPECS

# Reuse shared footer band from oil & gas assets.
FOOTER_BAND_PATH = (
    Path(__file__).resolve().parents[1] / 'oil_gas' / 'report_assets' / 'band_bottom.png'
)

PAGE_WIDTH = 595.28
PAGE_HEIGHT = 841.89
MARGIN_X = 28.0
TEAL = (0.05, 0.27, 0.30)
BLACK = (0.08, 0.08, 0.08)
HEADER_FILL = (0.82, 0.90, 0.82)
GRID = (0.55, 0.55, 0.55)

UNIT_AR = {
    'MW': 'ميغاواط',
    'MWh': 'ميغاواط ساعي',
    't': 'طن',
    't/d': 'طن/يوم',
    'Hz': 'هرتز',
    '%': '%',
    'M m³/d': 'مليون م٣/يوم',
    'count': 'عدد',
}


def _fmt_date(report_date: date) -> str:
    return f'{report_date.day}/{report_date.month}/{report_date.year}'


def _fmt_value(value: Any) -> str:
    if value is None:
        return '—'
    try:
        number = Decimal(str(value))
    except Exception:
        return str(value)
    if number == number.to_integral_value():
        return f'{int(number):,}'
    quantized = number.quantize(Decimal('0.01')).normalize()
    return f'{quantized}'.replace('.', ',')


def _unit_ar(unit: str) -> str:
    return UNIT_AR.get(unit, unit)


def _write_en(
    tw: fitz.TextWriter,
    x: float,
    y: float,
    text: str,
    font: fitz.Font,
    fontsize: float,
) -> None:
    tw.append(fitz.Point(x, y), text, font=font, fontsize=fontsize)


def build_electricity_report_pdf_bytes(report_date: date) -> bytes | None:
    payload = build_info_report_detail_payload(report_date)
    if not payload:
        return None
    if not FOOTER_BAND_PATH.is_file():
        raise FileNotFoundError('Electricity report PDF assets are missing.')

    ar = ArabicPdfText()
    date_label = _fmt_date(report_date)
    metrics_by_key = {
        row['metric_key']: row for row in (payload.get('metrics') or []) if row.get('metric_key')
    }

    ordered_specs = sorted(
        METRIC_SPECS,
        key=lambda s: (s.kpi_order is None, s.kpi_order or 999, s.category, s.key),
    )
    table_rows: list[tuple[str, str, str]] = []
    for spec in ordered_specs:
        row = metrics_by_key.get(spec.key)
        if not row or row.get('value') is None:
            continue
        table_rows.append(
            (
                spec.label_ar,
                _fmt_value(row.get('value')),
                _unit_ar(row.get('unit') or spec.unit),
            )
        )

    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    tw_teal = fitz.TextWriter(page.rect)

    header_h = 118.0  # tighter under logo; gold rule sits above title
    draw_electricity_letterhead(
        page,
        fitz.Rect(0, 0, PAGE_WIDTH, header_h),
        date_label=date_label,
    )

    y = header_h + 12  # space under raised gold rule before title
    right_x = PAGE_WIDTH - MARGIN_X
    left_x = MARGIN_X

    ar.write_baseline(
        page,
        left_x,
        y,
        right_x,
        'التقرير اليومي لقطاع الكهرباء',
        fontsize=13,
        bold=True,
        align='center',
    )
    y += 17

    ar.write_baseline(
        page, left_x, y, right_x, 'صالة التنسيق', fontsize=10, align='center',
    )
    y += 15

    ar.write_baseline(
        page,
        left_x,
        y,
        right_x,
        f'الموضوع: التقرير اليومي لتاريخ {date_label}',
        fontsize=10,
        bold=True,
        align='right',
    )
    y += 15

    table_left = MARGIN_X
    table_right = PAGE_WIDTH - MARGIN_X
    col_value_w = 62.0
    col_unit_w = 88.0
    x_unit = table_left
    x_value = x_unit + col_unit_w
    x_label = x_value + col_value_w
    header_h_row = 14.0
    band_h = 24.0
    # Closing block: please + thanks + director + name
    closing_h = 78.0
    footer_reserve = band_h + closing_h
    label_font = 8.0
    value_font = 8.0
    unit_font = 7.0

    # Fit all rows on this page by shrinking row height as needed.
    usable = PAGE_HEIGHT - footer_reserve - y - header_h_row
    n_rows = max(len(table_rows), 1)
    row_h = min(14.5, max(10.5, usable / n_rows))

    top = y
    bottom = top + header_h_row
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
    shape.finish(fill=HEADER_FILL, color=GRID, width=0.55)
    shape.commit()
    for x in (x_value, x_label):
        shape = page.new_shape()
        shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
        shape.finish(color=GRID, width=0.45)
        shape.commit()
    baseline = top + 10.5
    for text, x0, x1 in (
        ('الوحدة', x_unit, x_value),
        ('القيمة', x_value, x_label),
        ('البيان', x_label, table_right),
    ):
        ar.write_baseline(
            page, x0, baseline, x1, text, fontsize=9, bold=True, align='center',
        )
    y = bottom

    for label_ar, value_text, unit_logical in table_rows:
        top = y
        bottom = top + row_h
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
        shape.finish(color=GRID, width=0.4)
        shape.commit()
        for x in (x_value, x_label):
            shape = page.new_shape()
            shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
            shape.finish(color=GRID, width=0.4)
            shape.commit()

        mid_y = top + row_h / 2 + 2.4
        ar.write(
            page,
            fitz.Rect(x_unit + 1, top + 1, x_value - 1, bottom - 1),
            unit_logical,
            fontsize=unit_font,
            align='center',
        )
        vw = ar.en_width(value_text, value_font)
        _write_en(
            tw_teal,
            x_value + (col_value_w - vw) / 2,
            mid_y,
            value_text,
            ar.en_font,
            value_font,
        )
        ar.write(
            page,
            fitz.Rect(x_label + 2, top + 1, table_right - 2, bottom - 1),
            label_ar,
            fontsize=label_font,
            align='right',
        )
        y = bottom

    # Closing / signature directly under the table.
    y += 12
    ar.write_baseline(
        page, left_x, y, right_x, 'يُرجى التفضل بالاطلاع.', fontsize=10, align='right',
    )
    y += 14
    ar.write_baseline(
        page, left_x, y, right_x, 'شاكرين تعاونكم', fontsize=11, bold=True, align='center',
    )
    y += 16
    ar.write_baseline(
        page,
        left_x,
        y,
        PAGE_WIDTH / 2 - 8,
        'مدير إدارة تنظيم قطاع الكهرباء',
        fontsize=11,
        bold=True,
        align='left',
    )
    y += 15
    ar.write_baseline(
        page,
        left_x,
        y,
        PAGE_WIDTH / 2 - 8,
        'الدكتور شادي كلش',
        fontsize=13,
        bold=True,
        align='left',
    )

    tw_teal.write_text(page, color=TEAL)
    page.insert_image(
        fitz.Rect(0, PAGE_HEIGHT - band_h, PAGE_WIDTH, PAGE_HEIGHT),
        filename=str(FOOTER_BAND_PATH),
        keep_proportion=False,
    )

    apply_rtl_document(doc)
    buffer = BytesIO()
    doc.save(buffer, garbage=4, deflate=True)
    doc.close()
    return buffer.getvalue()


def export_electricity_report_pdf(report_date: date) -> HttpResponse | None:
    content = build_electricity_report_pdf_bytes(report_date)
    if content is None:
        return None
    filename = f'electricity_daily_report_{report_date.isoformat()}.pdf'
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
