"""Generate geology / mineral-resources ore production PDF report.

Reads from geology.info_dashboard.build_ore_production_info_dashboard(), which is
read-only against report_moe-owned Info data — no local write model involved.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import fitz
from config.pdf_arabic import ArabicPdfText, apply_rtl_document
from config.pdf_letterhead import draw_mineral_letterhead
from django.http import HttpResponse

from .info_dashboard import build_ore_production_info_dashboard

PAGE_WIDTH = 595.28
PAGE_HEIGHT = 841.89
MARGIN_X = 28.0
HEADER_FILL = (0.82, 0.90, 0.82)
GRID = (0.55, 0.55, 0.55)


def _fmt_qty(value: Any) -> str:
    if value is None:
        return '—'
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == int(number):
        return f'{int(number):,}'
    return f'{number:,.3f}'.rstrip('0').rstrip('.')


def _fmt_pct(value: Any) -> str:
    if value is None:
        return '—'
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f'{number:.2f}%'


def _kpis_from_totals(totals: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {'label_ar': 'أنواع المنتجات', 'value': totals.get('products'), 'unit': ''},
        {'label_ar': 'عدد العقود', 'value': totals.get('contracts'), 'unit': ''},
        {'label_ar': 'المخطط السنوي', 'value': totals.get('annual_plan'), 'unit': 'طن'},
        {'label_ar': 'المنفذ (النصف الأول)', 'value': totals.get('h1_executed'), 'unit': 'طن'},
    ]


def build_geology_report_pdf_bytes(plan_year: int) -> bytes | None:
    payload = build_ore_production_info_dashboard(plan_year=plan_year)
    if payload is None:
        return None
    rows = list(payload.get('rows') or [])
    kpis = _kpis_from_totals(payload.get('totals') or {})
    if not rows and not kpis:
        return None

    year = int(payload.get('plan_year') or plan_year)
    ar = ArabicPdfText()
    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

    header_h = 118.0
    draw_mineral_letterhead(
        page,
        fitz.Rect(0, 0, PAGE_WIDTH, header_h),
        date_label=str(year),
    )

    y = header_h + 12
    left_x = MARGIN_X
    right_x = PAGE_WIDTH - MARGIN_X

    ar.write_baseline(
        page,
        left_x,
        y,
        right_x,
        'تقرير إنتاج الخامات والعقود',
        fontsize=13,
        bold=True,
        align='center',
    )
    y += 16
    ar.write_baseline(
        page,
        left_x,
        y,
        right_x,
        f'سنة الخطة: {year}',
        fontsize=11,
        bold=True,
        align='center',
    )
    y += 18

    # KPI strip
    for kpi in kpis:
        label = kpi.get('label_ar') or kpi.get('label_en') or ''
        value = _fmt_qty(kpi.get('value'))
        unit = kpi.get('unit') or ''
        line = f'{label}: {value}' + (f' {unit}' if unit else '')
        ar.write_baseline(page, left_x, y, right_x, line, fontsize=10, align='right')
        y += 13
    y += 8

    if not rows:
        ar.write_baseline(
            page,
            left_x,
            y,
            right_x,
            'لا توجد صفوف إنتاج خامات لهذه السنة.',
            fontsize=10,
            align='center',
        )
    else:
        table_left = MARGIN_X
        table_right = PAGE_WIDTH - MARGIN_X
        # Columns (LTR left→right): unit | exec% | h1 exec | h1 plan | annual | type | product
        col_w = {
            'unit': 42.0,
            'pct': 48.0,
            'h1e': 58.0,
            'h1p': 58.0,
            'annual': 62.0,
            'ptype': 70.0,
        }
        used = sum(col_w.values())
        col_w['product'] = table_right - table_left - used
        xs = [table_left]
        for key in ('unit', 'pct', 'h1e', 'h1p', 'annual', 'ptype', 'product'):
            xs.append(xs[-1] + col_w[key])

        headers = (
            ('الوحدة', 0),
            ('نسبة التنفيذ', 1),
            ('منفذ ن1', 2),
            ('خطة ن1', 3),
            ('خطة سنوية', 4),
            ('نوع الإنتاج', 5),
            ('المنتج', 6),
        )
        row_h = 14.0
        header_h_row = 16.0
        band_h = 24.0
        footer_y = PAGE_HEIGHT - band_h - 36

        def ensure_space(needed: float) -> fitz.Page:
            nonlocal page, y, doc
            if y + needed <= footer_y:
                return page
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            y = MARGIN_X
            return page

        page = ensure_space(header_h_row + row_h)
        top = y
        bottom = top + header_h_row
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
        shape.finish(fill=HEADER_FILL, color=GRID, width=0.55)
        shape.commit()
        for x in xs[1:-1]:
            shape = page.new_shape()
            shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
            shape.finish(color=GRID, width=0.4)
            shape.commit()
        for text, idx in headers:
            ar.write(
                page,
                fitz.Rect(xs[idx] + 1, top + 1, xs[idx + 1] - 1, bottom - 1),
                text,
                fontsize=7,
                bold=True,
                align='center',
            )
        y = bottom

        for row in rows:
            page = ensure_space(row_h)
            top = y
            bottom = top + row_h
            shape = page.new_shape()
            shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
            shape.finish(color=GRID, width=0.35)
            shape.commit()
            for x in xs[1:-1]:
                shape = page.new_shape()
                shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
                shape.finish(color=GRID, width=0.3)
                shape.commit()

            cells = (
                (row.get('unit') or '—', 0, 'center'),
                (_fmt_pct(row.get('execution_pct')), 1, 'center'),
                (_fmt_qty(row.get('h1_executed_tons')), 2, 'center'),
                (_fmt_qty(row.get('h1_plan_tons')), 3, 'center'),
                (_fmt_qty(row.get('annual_plan_tons')), 4, 'center'),
                (row.get('production_type') or '—', 5, 'center'),
                (row.get('product_name_ar') or row.get('product_name_en') or '—', 6, 'right'),
            )
            for text, idx, align in cells:
                ar.write(
                    page,
                    fitz.Rect(xs[idx] + 1, top + 1, xs[idx + 1] - 1, bottom - 1),
                    str(text),
                    fontsize=7,
                    align=align,
                )
            y = bottom

    # Closing on last page
    y += 16
    if y > PAGE_HEIGHT - 60:
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        y = MARGIN_X + 20
    ar.write_baseline(
        page, left_x, y, right_x, 'يُرجى التفضل بالاطلاع.', fontsize=10, align='right',
    )
    y += 14
    ar.write_baseline(
        page, left_x, y, right_x, 'شاكرين تعاونكم', fontsize=11, bold=True, align='center',
    )

    apply_rtl_document(doc)
    buffer = BytesIO()
    doc.save(buffer, garbage=4, deflate=True)
    doc.close()
    return buffer.getvalue()


def export_geology_report_pdf(plan_year: int) -> HttpResponse | None:
    content = build_geology_report_pdf_bytes(plan_year)
    if content is None:
        return None
    filename = f'geology_ore_production_{plan_year}.pdf'
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
