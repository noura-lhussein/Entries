"""Seed static fuel-tank / hydro-dam / load-governorate catalogs for Info linking."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from electricity.operational_models import FuelTankStation, HydroDam, LoadGovernorate
from electricity.report_catalog import FUEL_TANK_STATIONS

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

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for station in FUEL_TANK_STATIONS:
            _, was = FuelTankStation.objects.update_or_create(
                code=station.code,
                defaults={
                    'name_ar': station.label_ar,
                    'name_en': station.label_en,
                    'max_capacity_tons': station.max_capacity_tons,
                },
            )
            created += int(was)
        for code, name_ar, name_en in HYDRO_DAMS:
            _, was = HydroDam.objects.update_or_create(
                code=code,
                defaults={'name_ar': name_ar, 'name_en': name_en},
            )
            created += int(was)
        for code, name_ar, name_en in LOAD_GOVERNORATES:
            _, was = LoadGovernorate.objects.update_or_create(
                code=code,
                defaults={'name_ar': name_ar, 'name_en': name_en},
            )
            created += int(was)
        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Fuel tanks={FuelTankStation.objects.count()}, '
                f'dams={HydroDam.objects.count()}, '
                f'govs={LoadGovernorate.objects.count()} (new/updated creates counted loosely={created}).'
            )
        )
