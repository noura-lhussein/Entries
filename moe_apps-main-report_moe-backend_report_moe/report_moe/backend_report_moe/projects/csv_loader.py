from __future__ import annotations

import csv
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from django.db import transaction
from django.utils import timezone

from .activity_provisioning import provision_project_activities
from .models import DevelopmentProject, ProjectGovernorate, ProjectOrganization

DEFAULT_DEVELOPMENT_PROJECT_CSV = Path(__file__).resolve().parents[2] / 'development_project.csv'

GOVERNORATE_CATALOG: dict[int, dict[str, str]] = {
    1: {'pcode': 'SY08', 'name_en': 'Al-Hasakeh', 'name_ar': 'الحسكة'},
    2: {'pcode': 'SY02', 'name_en': 'Aleppo', 'name_ar': 'حلب'},
    3: {'pcode': 'SY11', 'name_en': 'Ar-Raqqa', 'name_ar': 'الرقة'},
    4: {'pcode': 'SY09', 'name_en': 'As-Sweida', 'name_ar': 'السويداء'},
    5: {'pcode': 'SY01', 'name_en': 'Damascus', 'name_ar': 'دمشق'},
    6: {'pcode': 'SY14', 'name_en': "Dar'a", 'name_ar': 'درعا'},
    7: {'pcode': 'SY07', 'name_en': 'Deir-ez-Zor', 'name_ar': 'دير الزور'},
    8: {'pcode': 'SY04', 'name_en': 'Hama', 'name_ar': 'حماة'},
    9: {'pcode': 'SY03', 'name_en': 'Homs', 'name_ar': 'حمص'},
    10: {'pcode': 'SY10', 'name_en': 'Idleb', 'name_ar': 'إدلب'},
    11: {'pcode': 'SY06', 'name_en': 'Lattakia', 'name_ar': 'اللاذقية'},
    12: {'pcode': 'SY12', 'name_en': 'Quneitra', 'name_ar': 'القنيطرة'},
    13: {'pcode': 'SY13', 'name_en': 'Rural Damascus', 'name_ar': 'ريف دمشق'},
    14: {'pcode': 'SY05', 'name_en': 'Tartous', 'name_ar': 'طرطوس'},
}


def pcode_from_project_code(code: str) -> str:
    match = re.match(r'SYR-SY(\d+)-', code or '')
    if not match:
        return ''
    return f'SY{match.group(1).zfill(2)}'


def _parse_decimal(value: str | None) -> Decimal:
    if value is None or str(value).strip() == '':
        return Decimal('0')
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return Decimal('0')


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value).strip())


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return timezone.now()
    raw = str(value).strip()
    if raw.endswith('+03'):
        raw = raw[:-3] + '+0300'
    parsed = datetime.fromisoformat(raw)
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _parse_int(value: str | None) -> int | None:
    if value is None or str(value).strip() == '':
        return None
    return int(str(value).strip())


def ensure_reference_catalog(rows: list[dict[str, str]]) -> None:
    governorate_ids = {int(row['governorate_id']) for row in rows if row.get('governorate_id')}
    organization_ids = {int(row['organization_id']) for row in rows if row.get('organization_id')}

    for governorate_id in sorted(governorate_ids):
        meta = GOVERNORATE_CATALOG.get(
            governorate_id,
            {
                'pcode': '',
                'name_en': f'Governorate {governorate_id}',
                'name_ar': f'محافظة {governorate_id}',
            },
        )
        ProjectGovernorate.objects.update_or_create(
            id=governorate_id,
            defaults={
                'pcode': meta['pcode'],
                'name_en': meta['name_en'],
                'name_ar': meta['name_ar'],
            },
        )

    for organization_id in sorted(organization_ids):
        ProjectOrganization.objects.update_or_create(
            id=organization_id,
            defaults={
                'slug': f'org-{organization_id}',
                'acronym': f'O{organization_id}',
                'name_en': f'Institution {organization_id}',
            },
        )


def load_development_projects_csv(csv_path: Path | None = None) -> dict[str, int]:
    path = csv_path or DEFAULT_DEVELOPMENT_PROJECT_CSV
    if not path.is_file():
        raise FileNotFoundError(f'CSV not found: {path}')

    with path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))

    ensure_reference_catalog(rows)

    created = 0
    updated = 0
    skipped = 0

    with transaction.atomic():
        for row in rows:
            code = (row.get('code') or '').strip()
            if not code:
                skipped += 1
                continue

            governorate_id = int(row['governorate_id'])
            organization_id = int(row['organization_id'])
            governorate = ProjectGovernorate.objects.get(pk=governorate_id)
            organization = ProjectOrganization.objects.get(pk=organization_id)

            if not governorate.pcode:
                pcode = pcode_from_project_code(code)
                if pcode:
                    governorate.pcode = pcode
                    governorate.save(update_fields=['pcode'])

            defaults: dict[str, Any] = {
                'title_en': (row.get('title_en') or '').strip(),
                'title_ar': (row.get('title_ar') or '').strip(),
                'sector': (row.get('sector') or '').strip(),
                'status': (row.get('status') or 'active').strip(),
                'budget_usd': _parse_decimal(row.get('budget_usd')),
                'amount_spent_usd': _parse_decimal(row.get('amount_spent_usd')),
                'reporting_through': _parse_date(row.get('reporting_through')),
                'start_year': _parse_int(row.get('start_year')),
                'location': (row.get('location') or '').strip(),
                'created_at': _parse_datetime(row.get('created_at')),
                'updated_at': _parse_datetime(row.get('updated_at')),
                'governorate': governorate,
                'organization': organization,
                'is_active': True,
            }

            row_id = _parse_int(row.get('id'))
            lookup: dict[str, Any]
            if row_id is not None:
                lookup = {'id': row_id}
            else:
                lookup = {'code': code}

            defaults['code'] = code

            project, was_created = DevelopmentProject.objects.update_or_create(
                **lookup,
                defaults=defaults,
            )
            if was_created:
                provision_project_activities(project, with_example_actuals=False)
                created += 1
            else:
                updated += 1

    return {'created': created, 'updated': updated, 'skipped': skipped, 'total_rows': len(rows)}
