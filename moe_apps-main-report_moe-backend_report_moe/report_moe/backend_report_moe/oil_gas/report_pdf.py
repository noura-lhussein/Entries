"""Generate oil & gas executive daily report PDF matching MOE official letterhead."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz
from config.pdf_arabic import ArabicPdfText, apply_rtl_document
from config.pdf_letterhead import draw_oil_gas_letterhead
from django.http import HttpResponse

from .info_dashboard import build_info_dashboard_payload
from .metric_catalog import EXECUTIVE_METRIC_SPECS, resolve_metric_labels

ASSETS_DIR = Path(__file__).resolve().parent / 'report_assets'
FOOTER_BAND_PATH = ASSETS_DIR / 'band_bottom.png'

PAGE_WIDTH = 595.28  # A4
PAGE_HEIGHT = 841.89
MARGIN_X = 36.0
TEAL = (0.05, 0.27, 0.30)
BLACK = (0.08, 0.08, 0.08)
HEADER_FILL = (0.82, 0.90, 0.82)
GRID = (0.55, 0.55, 0.55)

UNIT_AR = {
    'bbl': 'برميل',
    'M m³': 'مليون م٣',
    'm³': 'م٣',
    'USD': 'دولار',
    'USD/bbl': 'دولار/ برميل',
    'USD/MMBtu': 'دولار',
}


def _fmt_date(report_date: date) -> str:
    return f'{report_date.day}/{report_date.month}/{report_date.year}'


def _fmt_value(value: Any, unit: str) -> str:
    if value is None:
        return '—'
    try:
        number = Decimal(str(value))
    except Exception:
        return str(value)
    unit_norm = (unit or '').replace(' ', '').lower()
    if 'mm³' in unit_norm or 'mm3' in unit_norm or unit == 'M m³':
        quantized = number.quantize(Decimal('0.001'))
        return f'{quantized}'.replace('.', ',')
    if 'usd' in unit_norm:
        quantized = number.quantize(Decimal('0.0001')).normalize()
        return f'{quantized}'.replace('.', ',')
    if number == number.to_integral_value():
        return f'{int(number):,}'
    return f'{number.normalize()}'


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


def build_oil_gas_report_pdf_bytes(report_date: date) -> bytes | None:
    info_payload = build_info_dashboard_payload(report_date)
    if not info_payload or info_payload.get('status') != 'ready':
        return None
    # Same {metric_key: {value, unit}} shape build_report_detail_payload used to
    # provide, sourced from Info kpis instead of the legacy DailyMetric table.
    payload = {
        'metrics': [
            {'metric_key': kpi.get('id'), 'value': kpi.get('value'), 'unit': kpi.get('unit')}
            for kpi in info_payload.get('kpis') or []
        ],
    }
    if not FOOTER_BAND_PATH.is_file():
        raise FileNotFoundError('Petroleum report PDF assets are missing.')

    ar = ArabicPdfText()
    date_label = _fmt_date(report_date)
    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    tw_en = fitz.TextWriter(page.rect)
    tw_teal = fitz.TextWriter(page.rect)

    header_h = 118.0
    draw_oil_gas_letterhead(
        page,
        fitz.Rect(0, 0, PAGE_WIDTH, header_h),
        date_label=date_label,
    )

    y = header_h + 14
    right_x = PAGE_WIDTH - MARGIN_X
    left_x = MARGIN_X

    ar.write_baseline(
        page, left_x, y, right_x, 'السيد الوزير', fontsize=16, bold=True, align='center',
    )
    y += 26

    ar.write_baseline(
        page,
        left_x,
        y,
        right_x,
        f'الموضوع: التقرير اليومي لتاريخ {date_label}',
        fontsize=12,
        bold=True,
        align='right',
    )
    y += 22

    intro_lines = (
        'في إطار المتابعة اليومية لواقع قطاع البترول ومشتقاته، نرفع إلى سيادتكم التقرير اليومي',
        f'المتضمن أبرز البيانات التشغيلية الخاصة بقطاع البترول والمنتجات البترولية ليوم ({date_label})',
    )
    for line in intro_lines:
        ar.write_baseline(page, left_x, y, right_x, line, fontsize=11, align='right')
        y += 15
    y += 9

    metrics_by_key = {
        row['metric_key']: row for row in (payload.get('metrics') or []) if row.get('metric_key')
    }
    table_left = MARGIN_X
    table_right = PAGE_WIDTH - MARGIN_X
    # RTL columns: البيان | القيمة | الوحدة  (LTR: unit | value | label)
    col_value_w = 70.0
    col_unit_w = 130.0
    x_unit = table_left
    x_value = x_unit + col_unit_w
    x_label = x_value + col_value_w
    row_h = 17.5
    header_h_row = 18.0
    unit_font_size = 8.0

    top = y
    bottom = top + header_h_row
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
    shape.finish(fill=HEADER_FILL, color=GRID, width=0.6)
    shape.commit()
    for x in (x_value, x_label):
        shape = page.new_shape()
        shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
        shape.finish(color=GRID, width=0.5)
        shape.commit()

    baseline = top + 13
    for text, x0, x1 in (
        ('الوحدة', x_unit, x_value),
        ('القيمة', x_value, x_label),
        ('البيان', x_label, table_right),
    ):
        ar.write_baseline(
            page, x0, baseline, x1, text, fontsize=10, bold=True, align='center',
        )
    y = bottom

    for spec in EXECUTIVE_METRIC_SPECS:
        row = metrics_by_key.get(spec.key)
        if not row:
            continue
        _label_en, label_ar = resolve_metric_labels(spec, report_date)
        unit = row.get('unit') or spec.unit
        value_text = _fmt_value(row.get('value'), unit)
        unit_logical = _unit_ar(unit)

        # Allow two lines for long unit labels.
        this_row_h = row_h if len(unit_logical) < 18 else 24.0
        top = y
        bottom = top + this_row_h
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
        shape.finish(color=GRID, width=0.45)
        shape.commit()
        for x in (x_value, x_label):
            shape = page.new_shape()
            shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
            shape.finish(color=GRID, width=0.45)
            shape.commit()

        mid_y = top + this_row_h / 2 + 3
        ar.write(
            page,
            fitz.Rect(x_unit + 2, top + 2, x_value - 2, bottom - 2),
            unit_logical,
            fontsize=unit_font_size,
            align='center',
        )

        vw = ar.en_width(value_text, 9)
        _write_en(
            tw_teal,
            x_value + (col_value_w - vw) / 2,
            mid_y,
            value_text,
            ar.en_font,
            9,
        )

        ar.write(
            page,
            fitz.Rect(x_label + 3, top + 2, table_right - 3, bottom - 2),
            label_ar,
            fontsize=9,
            align='right',
        )
        y = bottom

    y += 20
    ar.write_baseline(
        page, left_x, y, right_x, 'يُرجى التفضل بالاطلاع.', fontsize=11, align='right',
    )
    y += 18

    ar.write_baseline(
        page, left_x, y, right_x, 'شاكرين تعاونكم', fontsize=12, bold=True, align='center',
    )
    y += 28

    cc_y = y
    for i, raw in enumerate(
        ['صورة إلى :', 'مكتب معاون الوزير لشؤون التخطيط - لشؤون النفط']
    ):
        ar.write_baseline(
            page,
            PAGE_WIDTH / 2,
            cc_y,
            right_x,
            raw,
            fontsize=10,
            bold=(i == 0),
            align='right',
        )
        cc_y += 14

    # Signature at bottom-left of the page (physical left).
    sig_y = y + 36
    ar.write_baseline(
        page,
        left_x,
        sig_y,
        PAGE_WIDTH / 2 - 8,
        'مدير إدارة تنظيم قطاع البترول',
        fontsize=12,
        bold=True,
        align='left',
    )
    sig_y += 18
    ar.write_baseline(
        page,
        left_x,
        sig_y,
        PAGE_WIDTH / 2 - 8,
        'المهندس موسى الجبارة',
        fontsize=14,
        bold=True,
        align='left',
    )

    tw_en.write_text(page, color=BLACK)
    tw_teal.write_text(page, color=TEAL)

    band_h = 28.0
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


def export_oil_gas_report_pdf(report_date: date) -> HttpResponse | None:
    content = build_oil_gas_report_pdf_bytes(report_date)
    if content is None:
        return None
    filename = f'oil_gas_daily_report_{report_date.isoformat()}.pdf'
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
