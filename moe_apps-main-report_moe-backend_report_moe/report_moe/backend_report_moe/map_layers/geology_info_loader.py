from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

DEFAULT_GEOLOGY_INFO_CSV = Path(__file__).resolve().parents[2] / 'geology_info.csv'

CATEGORY_LABELS: dict[str, tuple[str, str]] = {
    'volcanic': ('Volcanic units', 'وحدات بركانية'),
    'sedimentary': ('Sedimentary units', 'وحدات رسوبية'),
    'modern': ('Modern (Quaternary) layers', 'طبقات حديثة (رباعية)'),
}


def _parse_bool(value: str | None) -> bool:
    return str(value or '').strip().lower() in ('1', 'true', 't', 'yes')


def _parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item).strip() for item in parsed if str(item).strip()]


def load_geology_info_catalog(csv_path: Path | None = None) -> list[dict[str, Any]]:
    """Load optional geology_info.csv rows.

    Not required for geology dashboard KPIs (those come from accepted Info only).
    Used by `/gis/geology-info/` and offline catalog tooling.
    """
    path = csv_path or DEFAULT_GEOLOGY_INFO_CSV
    if not path.is_file():
        return []

    rows: list[dict[str, Any]] = []
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not _parse_bool(row.get('is_active')):
                continue
            category = (row.get('category') or '').strip()
            label_en, label_ar = CATEGORY_LABELS.get(category, (category.title(), category))
            rows.append(
                {
                    'slug': (row.get('slug') or '').strip(),
                    'category': category,
                    'category_label': label_en,
                    'category_label_ar': label_ar,
                    'title_en': (row.get('title_en') or '').strip(),
                    'title_ar': (row.get('title_ar') or '').strip(),
                    'description_en': (row.get('description') or '').strip(),
                    'description_ar': (row.get('description_ar') or '').strip(),
                    'benefits': _parse_json_list(row.get('benefits')),
                    'benefits_ar': _parse_json_list(row.get('benefits_ar')),
                    'match_litho_type': (row.get('match_litho_type') or '').strip(),
                    'match_era': (row.get('match_era') or '').strip(),
                    'match_keywords': (row.get('match_keywords') or '').strip(),
                    'is_category_default': _parse_bool(row.get('is_category_default')),
                    'display_order': int(row.get('display_order') or 0),
                }
            )

    rows.sort(key=lambda item: (item['display_order'], item['slug']))
    return rows
