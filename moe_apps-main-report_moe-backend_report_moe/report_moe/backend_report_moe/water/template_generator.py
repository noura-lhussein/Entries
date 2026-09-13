from __future__ import annotations

import io
from pathlib import Path
from typing import Callable

from django.http import HttpResponse

try:
    import xlwt
except ImportError:
    xlwt = None

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None


def _xls_response(filename: str, build_sheet: Callable) -> HttpResponse:
    if xlwt is None:
        raise RuntimeError('xlwt is required for .xls templates')
    workbook = xlwt.Workbook()
    build_sheet(workbook.add_sheet('Sheet1'))
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.ms-excel',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _xlsx_response(filename: str, build_rows: Callable[[], list[list]]) -> HttpResponse:
    if Workbook is None:
        raise RuntimeError('openpyxl is required for .xlsx templates')
    workbook = Workbook()
    sheet = workbook.active
    for row in build_rows():
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def multisheet_xlsx_response(filename: str, sheets: dict[str, list[list]]) -> HttpResponse:
    if Workbook is None:
        raise RuntimeError('openpyxl is required for .xlsx templates')
    workbook = Workbook()
    workbook.remove(workbook.active)
    for title, rows in sheets.items():
        sheet = workbook.create_sheet(title=title[:31])
        for row in rows:
            sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def write_multisheet_xlsx_file(path: Path | str, sheets: dict[str, list[list]]) -> None:
    if Workbook is None:
        raise RuntimeError('openpyxl is required for .xlsx templates')
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    workbook.remove(workbook.active)
    for title, rows in sheets.items():
        sheet = workbook.create_sheet(title=title[:31])
        for row in rows:
            sheet.append(row)
    workbook.save(target)


def rainfall_template_response() -> HttpResponse:
    headers = ['المحطة', 'المحافظة', 'التاريخ',
               'كمية الهطول', 'ملاحظات', 'X', 'Y']
    sample = ['محطة 1', 'دمشق', '2026-04-01', 12.5, '', 500000, 7000000]

    def build(sheet):
        for col, value in enumerate(headers):
            sheet.write(0, col, value)
        for col, value in enumerate(sample):
            sheet.write(1, col, value)

    return _xls_response('rainfall_template.xls', build)


def dam_metadata_template_response() -> HttpResponse:
    headers = [
        'السد', 'المحافظة', 'X', 'Y', 'ملاحظات', 'نوع السد',
        'ارتفاع السد م', 'طول السد م', 'حجم التخزين الأعظمي م.م3',
        'الحجم الميت', 'تاريخ إنشاء  السد', 'الهدف من السد',
    ]
    sample = ['سد示例', 'دمشق', 500000, 7000000,
              '', 'ترابي', 25, 120, 50, 5, 1980, 'ري']

    def build(sheet):
        for col, value in enumerate(headers):
            sheet.write(0, col, value)
        for col, value in enumerate(sample):
            sheet.write(1, col, value)

    return _xls_response('dam_metadata_template.xls', build)


def dam_storage_template_response() -> HttpResponse:
    headers = ['المحافظة', 'السد', 'التاريخ',
               'حجم التخزين مليون.م3', 'ملاحظات']
    sample = ['دمشق', 'سد示例', '2026-04-01', 42.5, '']

    def build(sheet):
        for col, value in enumerate(headers):
            sheet.write(0, col, value)
        for col, value in enumerate(sample):
            sheet.write(1, col, value)

    return _xls_response('dam_storage_template.xls', build)


def euphrates_template_response() -> HttpResponse:
    title = 'المعلومات المائية والكهربائية لسدود الفرات خلال شهر / نيسان/ لعام 2026'
    headers = [
        'التاريخ', 'وارد جرابلس', 'منسوب تشرين', 'مخزون تشرين', 'ممرر تشرين',
        'توليد تشرين', 'منسوب الفرات', 'مخزون الفرات', 'ممرر الفرات',
        'توليد الفرات', 'ممرر كديران', 'توليد كديران', 'ممرر الجلاب', 'إجمالي التوليد',
    ]
    sample = [
        '2026-04-01', 1200, 326.5, 1.75, 800, 2100, 302.1, 12.09, 1500, 4500, 200, 570, 0, 7175,
    ]

    def rows():
        yield [title] + [''] * (len(headers) - 1)
        yield headers
        yield sample

    return _xlsx_response('euphrates_template.xlsx', rows)
