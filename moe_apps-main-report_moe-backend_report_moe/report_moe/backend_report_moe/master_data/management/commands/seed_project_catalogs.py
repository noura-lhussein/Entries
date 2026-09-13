"""
Seed project governorates and organizations catalogs into schema `moeds`.

Ported from moeds `projects/csv_loader.py::ensure_reference_catalog()`. report_moe is
the single writer for project reference tables, so this seeder lives here; moeds can
only read them.

The catalogs are static references for governorate codes and institution IDs. They're
created from the development_project.csv file to ensure consistency.

Usage:
  python manage.py seed_project_catalogs
  python manage.py seed_project_catalogs --csv path/to/development_project.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from master_data.models import ProjectGovernorate, ProjectOrganization

DEFAULT_DEVELOPMENT_PROJECT_CSV = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent / 'moeds' / 'moe-backend' / 'development_project.csv'
)

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



class Command(BaseCommand):
    help = 'Seed project governorate and organization catalogs from development_project.csv.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default=str(DEFAULT_DEVELOPMENT_PROJECT_CSV),
            help='Path to development_project.csv',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv'])
        if csv_path.is_file():
            try:
                with csv_path.open(encoding='utf-8-sig', newline='') as handle:
                    rows = list(csv.DictReader(handle))
                governorate_ids = {int(row['governorate_id']) for row in rows if row.get('governorate_id')}
                organization_ids = {int(row['organization_id']) for row in rows if row.get('organization_id')}
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'Failed to read CSV: {exc}'))
                governorate_ids = set()
                organization_ids = set()
        else:
            self.stdout.write(self.style.WARNING(f'CSV not found: {csv_path}, seeding static catalogs only'))
            governorate_ids = set(GOVERNORATE_CATALOG.keys())
            organization_ids = set()

        # If no IDs from CSV, seed all static governorates
        if not governorate_ids:
            governorate_ids = set(GOVERNORATE_CATALOG.keys())

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

        govs = ProjectGovernorate.objects.count()
        orgs = ProjectOrganization.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded project catalogs: {govs} governorates, {orgs} organizations.'
            )
        )
