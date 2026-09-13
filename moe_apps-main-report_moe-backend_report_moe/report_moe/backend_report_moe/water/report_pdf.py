"""Generate per-section water-resources dashboard PDF reports."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import fitz
from config.api_errors import detail_error
from config.pdf_arabic import ArabicPdfText, apply_rtl_document
from config.pdf_letterhead import draw_water_letterhead
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
from .report_export import WATER_EXPORT_SECTIONS

PAGE_WIDTH = 595.28
PAGE_HEIGHT = 841.89
MARGIN_X = 28.0
HEADER_FILL = (0.82, 0.90, 0.82)
GRID = (0.55, 0.55, 0.55)

_SECTION_TITLES = {
    'rainfall': 'تقرير الأمطار',
    'dams': 'تقرير السدود',
    'euphrates': 'تقرير منظومة الفرات',
    'drinking-water': 'تقرير مياه الشرب',
}


def _fmt(value: Any) -> str:
    if value is None:
        return '—'
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == int(number):
        return f'{int(number):,}'
    return f'{number:,.2f}'.rstrip('0').rstrip('.')


def _write_kpi_table(
    page: fitz.Page,
    ar: ArabicPdfText,
    *,
    y: float,
    title: str,
    kpis: list[dict[str, Any]],
) -> float:
    left_x = MARGIN_X
    right_x = PAGE_WIDTH - MARGIN_X
    ar.write_baseline(page, left_x, y, right_x, title, fontsize=11, bold=True, align='right')
    y += 14
    if not kpis:
        ar.write_baseline(page, left_x, y, right_x, 'لا توجد مؤشرات.', fontsize=9, align='right')
        return y + 14

    table_left = MARGIN_X
    table_right = PAGE_WIDTH - MARGIN_X
    col_unit = 70.0
    col_value = 90.0
    x_unit = table_left
    x_value = x_unit + col_unit
    x_label = x_value + col_value
    row_h = 13.0
    header_h = 14.0

    top = y
    bottom = top + header_h
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
    shape.finish(fill=HEADER_FILL, color=GRID, width=0.5)
    shape.commit()
    for x in (x_value, x_label):
        shape = page.new_shape()
        shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
        shape.finish(color=GRID, width=0.35)
        shape.commit()
    for text, x0, x1 in (
        ('الوحدة', x_unit, x_value),
        ('القيمة', x_value, x_label),
        ('المؤشر', x_label, table_right),
    ):
        ar.write(
            page,
            fitz.Rect(x0 + 1, top + 1, x1 - 1, bottom - 1),
            text,
            fontsize=8,
            bold=True,
            align='center',
        )
    y = bottom

    for kpi in kpis:
        top = y
        bottom = top + row_h
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(table_left, top, table_right, bottom))
        shape.finish(color=GRID, width=0.3)
        shape.commit()
        for x in (x_value, x_label):
            shape = page.new_shape()
            shape.draw_line(fitz.Point(x, top), fitz.Point(x, bottom))
            shape.finish(color=GRID, width=0.25)
            shape.commit()
        ar.write(
            page,
            fitz.Rect(x_unit + 1, top + 1, x_value - 1, bottom - 1),
            str(kpi.get('unit') or '—'),
            fontsize=8,
            align='center',
        )
        ar.write(
            page,
            fitz.Rect(x_value + 1, top + 1, x_label - 1, bottom - 1),
            _fmt(kpi.get('value')),
            fontsize=8,
            align='center',
        )
        ar.write(
            page,
            fitz.Rect(x_label + 2, top + 1, table_right - 2, bottom - 1),
            str(kpi.get('label_ar') or kpi.get('label_en') or '—'),
            fontsize=8,
            align='right',
        )
        y = bottom
    return y + 12


def _write_simple_rows(
    page: fitz.Page,
    ar: ArabicPdfText,
    *,
    y: float,
    title: str,
    rows: list[tuple[str, str]],
) -> float:
    left_x = MARGIN_X
    right_x = PAGE_WIDTH - MARGIN_X
    ar.write_baseline(page, left_x, y, right_x, title, fontsize=11, bold=True, align='right')
    y += 13
    for label, value in rows:
        ar.write_baseline(
            page, left_x, y, right_x, f'{label}: {value}', fontsize=9, align='right',
        )
        y += 12
    return y + 8


def _closing(page: fitz.Page, ar: ArabicPdfText, y: float) -> None:
    left_x = MARGIN_X
    right_x = PAGE_WIDTH - MARGIN_X
    if y > PAGE_HEIGHT - 60:
        return
    ar.write_baseline(
        page, left_x, y, right_x, 'يُرجى التفضل بالاطلاع.', fontsize=10, align='right',
    )
    y += 14
    ar.write_baseline(
        page, left_x, y, right_x, 'شاكرين تعاونكم', fontsize=11, bold=True, align='center',
    )


def build_water_report_pdf_bytes(
    *,
    section: str,
    year: int | None = None,
    month: str | None = None,
    basin: str | None = None,
    governorate: str | None = None,
) -> tuple[bytes, str]:
    key = (section or '').strip().lower()
    if key not in WATER_EXPORT_SECTIONS:
        raise detail_error('section must be rainfall, dams, euphrates, or drinking-water.')

    if key == 'rainfall':
        payload = build_rainfall_dashboard_payload(
            year=year, basin_slug=basin, governorate=governorate,
        ) or {}
        period = str(payload.get('selected_year') or year or '')
        # Info-sourced rows carry a single `name`, not name_ar/name_en.
        extra_rows = [
            (row.get('name') or '—', _fmt(row.get('total_mm')) + ' مم')
            for row in ((payload.get('charts') or {}).get('top_stations') or [])[:10]
        ]
        extra_title = 'أعلى المحطات'
        stem = f'water_rainfall_report_{period or "latest"}'
    elif key == 'dams':
        if governorate:
            raise detail_error(
                'Dams export does not yet support governorate filtering on the Info-based dashboard.',
            )
        payload = build_dams_dashboard_payload(year=year, governorate=None) or {}
        period = str(payload.get('selected_year') or year or '')
        extra_rows = [
            (row.get('name') or '—', _fmt(row.get('storage_mcm')) + ' MCM')
            for row in ((payload.get('charts') or {}).get('top_dams') or [])[:10]
        ]
        extra_title = 'أعلى السدود مخزوناً'
        stem = f'water_dams_report_{period or "latest"}'
    elif key == 'euphrates':
        payload = build_euphrates_dashboard_payload(month=month) or {}
        period = str(payload.get('selected_month') or month or '')
        extra_rows = []
        for block_key, block in (payload.get('month_summary') or {}).items():
            if isinstance(block, dict):
                label = block.get('label_ar') or block.get('label_en') or block_key
                unit = block.get('unit') or ''
                extra_rows.append((str(label), f'{_fmt(block.get("value"))} {unit}'.strip()))
        for dam in (payload.get('dams') or [])[:8]:
            name = dam.get('name_ar') or dam.get('name_en') or '—'
            storage_bcm = dam.get('storage_bcm')
            max_storage_bcm = dam.get('max_storage_bcm')
            fill_pct = (
                round(storage_bcm / max_storage_bcm * 100, 1)
                if storage_bcm is not None and max_storage_bcm
                else None
            )
            extra_rows.append(
                (str(name), f'{_fmt(storage_bcm)} BCM / {_fmt(fill_pct)}%')
            )
        extra_title = 'ملخص المنظومة'
        stem = f'water_euphrates_report_{(period or "latest").replace("/", "-")}'
    else:
        payload = build_drinking_water_dashboard_payload()
        period = str(payload.get('selected_enrollment_year') or '')
        extra_rows = [
            ('عدد المحطات', _fmt(payload.get('data_total'))),
            ('المحافظة', str(payload.get('selected_governorate') or 'الكل')),
        ]
        extra_title = 'ملخص'
        stem = 'water_drinking_water_report'

    ar = ArabicPdfText()
    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    header_h = 118.0
    draw_water_letterhead(
        page,
        fitz.Rect(0, 0, PAGE_WIDTH, header_h),
        date_label=period,
    )

    y = header_h + 12
    left_x = MARGIN_X
    right_x = PAGE_WIDTH - MARGIN_X
    ar.write_baseline(
        page,
        left_x,
        y,
        right_x,
        _SECTION_TITLES[key],
        fontsize=13,
        bold=True,
        align='center',
    )
    y += 16
    if period:
        ar.write_baseline(
            page,
            left_x,
            y,
            right_x,
            f'الفترة المرجعية: {period}',
            fontsize=10,
            bold=True,
            align='center',
        )
        y += 16

    y = _write_kpi_table(
        page,
        ar,
        y=y,
        title='المؤشرات الرئيسية',
        kpis=list(payload.get('kpis') or []),
    )
    if extra_rows:
        if y > PAGE_HEIGHT - 120:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            y = MARGIN_X + 10
        y = _write_simple_rows(page, ar, y=y, title=extra_title, rows=extra_rows)

    _closing(page, ar, y + 8)

    apply_rtl_document(doc)
    buffer = BytesIO()
    doc.save(buffer, garbage=4, deflate=True)
    doc.close()
    return buffer.getvalue(), stem


def export_water_report_pdf(
    *,
    section: str,
    year: int | None = None,
    month: str | None = None,
    basin: str | None = None,
    governorate: str | None = None,
) -> HttpResponse:
    content, stem = build_water_report_pdf_bytes(
        section=section,
        year=year,
        month=month,
        basin=basin,
        governorate=governorate,
    )
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{stem}.pdf"'
    return response
