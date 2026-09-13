"""
Seed static fuel-tank / hydro-dam / load-governorate catalogs into schema `moeds`.

Ported from moeds `electricity/management/commands/seed_electricity_daily_catalogs.py`.
report_moe is the single writer for these three tables, so the seeder lives here;
moeds can only read them.

Usage:
  python manage.py seed_electricity_daily_catalogs
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from master_data.models import FuelTankStation, HydroDam, LoadGovernorate

FUEL_TANK_STATIONS = (
    ('tishreen', 'تشرين', 'Tishreen', 45000),
    ('banias', 'بانياس', 'Banias', 55000),
)

HYDRO_DAMS = (
    ('thawra', 'الثورة', 'Thawra (Revolution)'),
    ('euphrates', 'الفرات', 'Euphrates'),
    ('tishreen', 'تشرين', 'Tishreen'),
)

LOAD_GOVERNORATES = (
    ('damascus', 'دمشق', 'Damascus'),
    ('rif_damascus', 'ريف دمشق', 'Rif Damascus'),
    ('sweida', 'السويداء', 'Sweida'),
    ('daraa', 'درعا', 'Daraa'),
    ('quneitra', 'القنيطرة', 'Quneitra'),
    ('homs', 'حمص', 'Homs'),
    ('hama', 'حماة', 'Hama'),
    ('tartous', 'طرطوس', 'Tartous'),
    ('latakia', 'اللاذقية', 'Latakia'),
    ('aleppo', 'حلب', 'Aleppo'),
    ('deir_ez_zor', 'دير الزور', 'Deir ez-Zor'),
    ('raqqa', 'الرقة', 'Raqqa'),
    ('hasakah', 'الحسكة', 'Hasakah'),
)



class Command(BaseCommand):
    help = 'Seed FuelTankStation / HydroDam / LoadGovernorate static catalogs.'

    def handle(self, *args, **options):
        created = updated = 0
        with transaction.atomic():
            for code, name_ar, name_en, capacity in FUEL_TANK_STATIONS:
                _, was = FuelTankStation.objects.update_or_create(
                    code=code,
                    defaults={
                        'name_ar': name_ar,
                        'name_en': name_en,
                        'max_capacity_tons': capacity,
                    },
                )
                if was:
                    created += 1
                else:
                    updated += 1

            for code, name_ar, name_en in HYDRO_DAMS:
                _, was = HydroDam.objects.update_or_create(
                    code=code,
                    defaults={'name_ar': name_ar, 'name_en': name_en},
                )
                if was:
                    created += 1
                else:
                    updated += 1

            for code, name_ar, name_en in LOAD_GOVERNORATES:
                _, was = LoadGovernorate.objects.update_or_create(
                    code=code,
                    defaults={'name_ar': name_ar, 'name_en': name_en},
                )
                if was:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded catalogs: created={created}, updated={updated}. '
                f'Fuel tanks={FuelTankStation.objects.count()}, '
                f'dams={HydroDam.objects.count()}, '
                f'govs={LoadGovernorate.objects.count()}.'
            )
        )
