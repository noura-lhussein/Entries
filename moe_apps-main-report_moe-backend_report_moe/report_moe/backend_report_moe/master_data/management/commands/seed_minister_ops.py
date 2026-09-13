"""
Seed oil & gas master data: fields, wells, refineries, pipelines, fuel stations.

Ported from moeds `oil_gas/management/commands/seed_minister_ops.py`. report_moe is the
single writer for these catalogs, so the seeder lives here; moeds reads them.

This command seeds only the master/catalog data. Operational data (daily production,
reports, snapshots, alerts) remains in moeds and is seeded separately.

Usage:
  python manage.py seed_minister_ops
  python manage.py seed_minister_ops --anchor-date 2026-04-01 --days 30
"""

from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from master_data.models import OilFacility as Facility
from master_data.models import OilField as Field
from master_data.models import OilPipeline as Pipeline
from master_data.models import OilRefinery as Refinery


class Command(BaseCommand):
    help = 'Seed oil & gas master data: fields, wells, refineries, pipelines, fuel stations.'

    def handle(self, *args, **options):
        with transaction.atomic():
            self._seed_fields()
            self._seed_refineries()
            self._seed_pipelines()
            self._seed_fuel_stations()
        self.stdout.write(self.style.SUCCESS('Oil & gas master data seeded.'))

    def _seed_fields(self):
        field_specs = [
            ('FURAT', 'حقل الفرات', 'Al-Furat Field', Field.FieldType.OIL, Field.Status.ACTIVE, 18000),
            ('TAYM', 'حقل التيم', 'Al-Taym Field', Field.FieldType.OIL, Field.Status.SHUTDOWN, 8000),
            ('DEIR', 'دير الزور', 'Deir ez-Zor Field', Field.FieldType.OIL, Field.Status.ACTIVE, 9000),
            ('EBLA', 'حيان / إيبلا', 'Ebla & Hayyan', Field.FieldType.GAS, Field.Status.ACTIVE, 5000),
        ]
        for code, ar, en, ftype, status, cap in field_specs:
            Field.objects.update_or_create(
                code=code,
                defaults={
                    'name_ar': ar,
                    'name_en': en,
                    'field_type': ftype,
                    'governorate': 'Homs',
                    'status': status,
                    'design_capacity_bpd': Decimal(cap),
                    'operator_company': 'Syrian Petroleum Company',
                },
            )

    def _seed_refineries(self):
        Refinery.objects.update_or_create(
            refinery_name='Homs Refinery',
            defaults={
                'name_ar': 'مصفاة حمص للنفط',
                'governorate': 'Homs',
                'latitude': Decimal('34.729100'),
                'longitude': Decimal('36.666900'),
                'status': Refinery.Status.OPERATING,
                'design_capacity_bpd': Decimal('120000'),
                'notes': 'منشأة التكرير المركزية التي تغذي شبكات الطاقة المحلية.',
            },
        )
        Refinery.objects.update_or_create(
            refinery_name='Banias Refinery',
            defaults={
                'name_ar': 'مصفاة ومصب بانياس',
                'governorate': 'Tartous',
                'latitude': Decimal('35.197200'),
                'longitude': Decimal('35.946300'),
                'status': Refinery.Status.OPERATING,
                'design_capacity_bpd': Decimal('130000'),
                'notes': 'المصب البحري الرئيسي ومجمع تكرير النفط على الساحل السوري.',
            },
        )

    def _seed_pipelines(self):
        Pipeline.objects.update_or_create(
            name='East–West Crude Main Pipeline',
            defaults={
                'name_ar': 'خط أنابيب النفط الخام الرئيسي (شرق - غرب)',
                'source_location': 'Rmeilan',
                'destination_location': 'Banias',
                'source_latitude': Decimal('36.983300'),
                'source_longitude': Decimal('42.183300'),
                'dest_latitude': Decimal('35.197200'),
                'dest_longitude': Decimal('35.946300'),
                'path_coordinates': [
                    [42.1833, 36.9833],
                    [41.1215, 36.2118],
                    [40.6014, 35.0746],
                    [38.5411, 35.7234],
                    [36.6669, 34.7291],
                    [35.9463, 35.1972],
                ],
                'length_km': Decimal('650'),
                'design_capacity_bpd': Decimal('90000'),
                'status': Pipeline.Status.DEGRADED,
                'notes': 'ينقل النفط من حقول الرميلان والأنحاء الشرقية غرباً إلى مصفاة حمص وميناء بانياس.',
            },
        )
        Pipeline.objects.filter(name='Banias–Homs Crude Line').update(
            source_latitude=Decimal('35.197200'),
            source_longitude=Decimal('35.946300'),
            dest_latitude=Decimal('34.729100'),
            dest_longitude=Decimal('36.666900'),
        )

    def _seed_fuel_stations(self):
        fuel_station_specs = [
            (
                'damascus-central-station',
                'Damascus Central Station',
                'محطة دمشق المركزية',
                'Damascus',
                Decimal('33.513800'),
                Decimal('36.276500'),
            ),
            (
                'homs-fuel-station',
                'Homs Fuel Station',
                'محطة حمص للوقود',
                'Homs',
                Decimal('34.729100'),
                Decimal('36.666900'),
            ),
            (
                'banias-fuel-station',
                'Banias Fuel Station',
                'محطة بانياس للوقود',
                'Tartous',
                Decimal('35.197200'),
                Decimal('35.946300'),
            ),
        ]
        for code, en, ar, gov, lat, lng in fuel_station_specs:
            Facility.objects.update_or_create(
                code=code,
                defaults={
                    'name_en': en,
                    'name_ar': ar,
                    'facility_type': Facility.FacilityType.FUEL_STATION,
                    'sector': Facility.Sector.OIL_GAS,
                    'governorate': gov,
                    'latitude': lat,
                    'longitude': lng,
                    'status': Facility.Status.ACTIVE,
                },
            )
