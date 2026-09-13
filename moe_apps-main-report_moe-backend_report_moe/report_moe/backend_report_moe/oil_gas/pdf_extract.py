"""Parse oil & gas executive daily report PDFs into structured metric dicts."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from .metric_catalog import EXECUTIVE_METRIC_KEYS, EXECUTIVE_OPTIONAL_METRIC_KEYS

ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

# Order matters — more specific labels first.
METRIC_LINE_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r'إجمالي\s*إنتاج\s*النفط', 'total_oil_production_bbl', 'bbl'),
    # PDF often inserts a space after the shadda: المُ رحل
    (r'إجمالي\s*النفط\s*الخام\s*الم\u064f?\s*رحل', 'total_crude_transferred_bbl', 'bbl'),
    (r'الإنتاج\s*المحلي\s*من\s*الغاز\s*النظيف', 'local_clean_gas_mm3', 'mm3'),
    (r'الغاز\s*النظيف\s*المستورد\s*من\s*أذربيجان', 'clean_gas_import_azerbaijan_mm3', 'mm3'),
    (r'الغاز\s*النظيف\s*المستورد\s*من\s*الأردن', 'clean_gas_import_jordan_mm3', 'mm3'),
    (r'مجموع\s*كميات\s*الغاز\s*النظيف\s*الموزعة', 'clean_gas_distributed_mm3', 'mm3'),
    (r'استهلاك\s*قطاع\s*الكهرباء\s*من\s*الغاز\s*النظيف', 'electricity_clean_gas_consumption_mm3', 'mm3'),
    (r'إجمالي\s*الغاز\s*النظيف', 'total_clean_gas_mm3', 'mm3'),
    (r'كميات\s*المازوت', 'mazut_sold_thu_fri_m3', 'm3'),
    (r'كميان?\s*البنزين', 'gasoline_90_95_sold_thu_fri_m3', 'm3'),
    (r'كميات\s*الغاز\s*الم[ُu]?\s*سال', 'domestic_lpg_sold_m3', 'm3'),
    (r'كميات\s*الفيول', 'fuel_oil_sold_m3', 'm3'),
    (r'سعر\s*النفط\s*كخام\s*برنت', 'brent_crude_price_usd_bbl', 'usd'),
    (r'سعر\s*الغاز', 'gas_price_usd_mmbtu', 'usd'),
)

# Newer PDF exports often reverse Arabic glyphs; values still appear in fixed order.
RTL_ORDERED_METRICS: tuple[tuple[str, str], ...] = (
    ('total_oil_production_bbl', 'bbl'),
    ('total_crude_transferred_bbl', 'bbl'),
    ('local_clean_gas_mm3', 'mm3'),
    ('clean_gas_import_azerbaijan_mm3', 'mm3'),
    ('clean_gas_import_jordan_mm3', 'mm3'),
    ('total_clean_gas_mm3', 'mm3'),
    ('clean_gas_distributed_mm3', 'mm3'),
    ('electricity_clean_gas_consumption_mm3', 'mm3'),
    ('mazut_sold_thu_fri_m3', 'm3'),
    ('gasoline_90_95_sold_thu_fri_m3', 'm3'),
    ('domestic_lpg_sold_m3', 'm3'),
    ('fuel_oil_sold_m3', 'm3'),
    ('brent_crude_price_usd_bbl', 'usd'),
    ('gas_price_usd_mmbtu', 'usd'),
)


def normalize(text: str) -> str:
    return text.translate(ARABIC_DIGITS)


def parse_number_token(raw: str, unit_kind: str) -> float | None:
    """Parse a numeric token using the same conventions as entered June reports."""
    token = normalize(raw).strip().replace(' ', '')
    if not token:
        return None

    # Some RTL PDF extracts corrupt thousands as "12,4.32" instead of "12,432".
    if unit_kind in ('bbl', 'm3') and ',' in token and '.' in token:
        token = token.replace('.', '')

    if unit_kind == 'usd':
        # 84,51 / 72.1024 / 11.31 — keep source precision (no rounding).
        match = re.fullmatch(r'(\d+)[.,](\d+)', token)
        if match:
            return float(f'{match.group(1)}.{match.group(2)}')
        match = re.search(r'\d+(?:\.\d+)?', token.replace(',', ''))
        return float(match.group()) if match else None

    if unit_kind == 'mm3':
        # Gas volumes are small; comma or dot is a decimal separator (7,172 → 7.172).
        match = re.fullmatch(r'(\d+)[.,](\d+)', token)
        if match:
            return round(float(f'{match.group(1)}.{match.group(2)}'), 3)
        match = re.search(r'\d+(?:\.\d+)?', token.replace(',', ''))
        return round(float(match.group()), 3) if match else None

    # bbl / m3: separator before exactly 3 digits is a thousands marker
    # (110.034 → 110034, 14,820 → 14820).
    match = re.fullmatch(r'(\d{1,3})[.,](\d{3})', token)
    if match:
        return float(f'{match.group(1)}{match.group(2)}')
    match = re.fullmatch(r'(\d+)[.,](\d{3})', token)
    if match:
        return float(f'{match.group(1)}{match.group(2)}')
    match = re.search(r'\d+(?:\.\d+)?', token.replace(',', ''))
    return float(match.group()) if match else None


def parse_value(raw: str, unit_kind: str) -> float | None:
    return parse_number_token(raw, unit_kind)


def parse_report_date_from_text(text: str) -> date | None:
    normalized = normalize(text)
    match = re.search(r'(?:لتاريخ|ليوم)\s*(\d{1,2})/(\d{1,2})/(\d{4})', normalized)
    if match:
        day, month, year = (int(match.group(i)) for i in range(1, 4))
        return date(year, month, day)
    return None


def parse_report_date_from_path(path: Path) -> date | None:
    normalized = normalize(path.stem)
    # تقرير 1-7-2026 ...
    match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', normalized)
    if match:
        day, month, year = (int(match.group(i)) for i in range(1, 4))
        return date(year, month, day)
    # تقرير_انتاج_..._بتاريخ_15_7_2026
    match = re.search(r'(?:بتاريخ[_-]?)?(\d{1,2})_(\d{1,2})_(\d{4})', normalized)
    if match:
        day, month, year = (int(match.group(i)) for i in range(1, 4))
        return date(year, month, day)
    return None


def _extract_number_from_line(line: str, unit_kind: str) -> float | None:
    if unit_kind == 'usd':
        match = re.search(r'([\d.,]+)\s*دولار', line)
        if match:
            return parse_number_token(match.group(1), unit_kind)
        match = re.search(r'([\d.,]+)', line)
        return parse_number_token(match.group(1), unit_kind) if match else None
    if unit_kind == 'mm3':
        match = re.search(r'([\d.,]+)\s*مليون\s*[mم]3', line)
    elif unit_kind == 'bbl':
        match = re.search(r'([\d.,]+)\s*برميل', line)
    else:
        match = re.search(r'([\d.,]+)\s*م3', line)
    if match:
        return parse_number_token(match.group(1), unit_kind)
    # RTL / number-first lines
    match = re.match(r'^\s*([\d.,]+)', line)
    return parse_number_token(match.group(1), unit_kind) if match else None


def _extract_label_metrics(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        for pattern, key, unit_kind in METRIC_LINE_PATTERNS:
            if key in metrics:
                continue
            if not re.search(pattern, stripped):
                continue
            value = _extract_number_from_line(stripped, unit_kind)
            if value is not None:
                metrics[key] = value
            break
    return metrics


def _extract_rtl_ordered_metrics(text: str) -> dict[str, float]:
    """Fallback for PDFs where Arabic labels are glyph-reversed but value order is fixed."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    start: int | None = None
    for index, line in enumerate(lines):
        # First oil line: number + reversed "برميل" (ليمرب)
        if re.match(r'^[\d.,]+\s*ليمرب', line) or (
            re.match(r'^[\d.,]+', line) and 'ليمرب' in line and 'إر' in line
        ):
            start = index
            break
        # Also accept first barrel line in a dense metric block
        if re.match(r'^[\d.,]+\s*ليمرب', line):
            start = index
            break
    if start is None:
        # Looser: first line starting with a large barrel-like number
        for index, line in enumerate(lines):
            match = re.match(r'^([\d.,]+)', line)
            if not match or 'ليمرب' not in line:
                continue
            value = parse_number_token(match.group(1), 'bbl')
            if value is not None and value >= 50_000:
                start = index
                break
    if start is None:
        return {}

    block = lines[start : start + len(RTL_ORDERED_METRICS)]
    if len(block) < len(RTL_ORDERED_METRICS):
        return {}

    metrics: dict[str, float] = {}
    for (key, unit_kind), line in zip(RTL_ORDERED_METRICS, block, strict=True):
        match = re.match(r'^([\d.,]+)', line)
        if not match:
            continue
        value = parse_number_token(match.group(1), unit_kind)
        if value is not None:
            metrics[key] = value
    return metrics


def _finalize_metrics(metrics: dict[str, float]) -> dict[str, float]:
    if all(
        key in metrics
        for key in (
            'local_clean_gas_mm3',
            'clean_gas_import_azerbaijan_mm3',
            'clean_gas_import_jordan_mm3',
        )
    ):
        metrics['total_clean_gas_mm3'] = round(
            metrics['local_clean_gas_mm3']
            + metrics['clean_gas_import_azerbaijan_mm3']
            + metrics['clean_gas_import_jordan_mm3'],
            3,
        )
    return metrics


def extract_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    text = normalize('\n'.join(page.extract_text() or '' for page in reader.pages))
    report_date = parse_report_date_from_text(text) or parse_report_date_from_path(path)
    if not report_date:
        raise ValueError(f'Could not parse report date from {path.name}')

    metrics = _extract_label_metrics(text)
    required = EXECUTIVE_METRIC_KEYS - EXECUTIVE_OPTIONAL_METRIC_KEYS
    if required - metrics.keys():
        rtl_metrics = _extract_rtl_ordered_metrics(text)
        # Prefer label hits; fill gaps from RTL ordered block.
        for key, value in rtl_metrics.items():
            metrics.setdefault(key, value)

    metrics = _finalize_metrics(metrics)

    missing = [key for key in required if key not in metrics]
    if missing:
        raise ValueError(f'Missing metrics in {path.name}: {", ".join(missing)}')

    return {
        'report_date': report_date,
        'metrics': metrics,
        'notes_ar': f'التقرير اليومي لقطاع البترول — {report_date.day}/{report_date.month}/{report_date.year}',
        'notes_en': f'Daily petroleum sector report — {report_date.isoformat()}',
    }
