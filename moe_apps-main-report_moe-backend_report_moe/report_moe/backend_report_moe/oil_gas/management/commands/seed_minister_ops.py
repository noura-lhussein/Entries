from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from oil_gas.alert_engine import evaluate_alerts
from oil_gas.models import (
    DailyProduction,
    DailyReport,
    Export,
    Facility,
    Field,
    FuelInventory,
    OperationalTarget,
    Pipeline,
    PowerGasRequirement,
    PowerGasSupply,
    ProductionLoss,
    Refinery,
    RefineryDailyOutput,
    Well,
)
from oil_gas.services import upsert_metric
from oil_gas.snapshot_builder import build_kpi_snapshot


class Command(BaseCommand):
    help = 'Seed minister operational data, KPI snapshots, and alerts.'

    def add_arguments(self, parser):
        parser.add_argument('--anchor-date', default='2026-03-25')
        parser.add_argument('--days', type=int, default=14)

    @transaction.atomic
    def handle(self, *args, **options):
        anchor = date.fromisoformat(options['anchor_date'])
        days = options['days']

        fields = self._seed_master_data()
        self.stdout.write(self.style.SUCCESS(f'Master data ready ({len(fields)} fields).'))
        self._seed_targets(anchor, days, fields)

        for offset in range(days - 1, -1, -1):
            d = anchor - timedelta(days=offset)
            day_index = days - 1 - offset
            self._seed_day(d, day_index, fields)
            snapshot = build_kpi_snapshot(d)
            evaluate_alerts(d, snapshot)

        self.stdout.write(self.style.SUCCESS(f'Seeded {days} days ending {anchor}.'))

    def _seed_master_data(self) -> list[Field]:
        field_specs = [
            ('FURAT', 'حقل الفرات', 'Al-Furat Field', Field.FieldType.OIL, Field.Status.ACTIVE, 18000),
            ('TAYM', 'حقل التيم', 'Al-Taym Field', Field.FieldType.OIL, Field.Status.SHUTDOWN, 8000),
            ('DEIR', 'دير الزور', 'Deir ez-Zor Field', Field.FieldType.OIL, Field.Status.ACTIVE, 9000),
            ('EBLA', 'حيان / إيبلا', 'Ebla & Hayyan', Field.FieldType.GAS, Field.Status.ACTIVE, 5000),
        ]
        fields = []
        for code, ar, en, ftype, status, cap in field_specs:
            field, _ = Field.objects.update_or_create(
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
            fields.append(field)

        self._seed_map_geojson_features()

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
                'notes': (
                    'ينقل النفط من حقول الرميلان والأنحاء الشرقية غرباً إلى مصفاة حمص وميناء بانياس.'
                ),
            },
        )
        # Keep legacy short Banias–Homs segment aligned with refinery endpoints when present.
        Pipeline.objects.filter(name='Banias–Homs Crude Line').update(
            source_latitude=Decimal('35.197200'),
            source_longitude=Decimal('35.946300'),
            dest_latitude=Decimal('34.729100'),
            dest_longitude=Decimal('36.666900'),
        )

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
                'محطة حمص',
                'Homs',
                Decimal('34.739500'),
                Decimal('36.716200'),
            ),
            (
                'aleppo-fuel-station',
                'Aleppo Fuel Station',
                'محطة حلب',
                'Aleppo',
                Decimal('36.202100'),
                Decimal('37.134300'),
            ),
        ]
        inventory_facility = None
        for code, name_en, name_ar, governorate, latitude, longitude in fuel_station_specs:
            station, _ = Facility.objects.update_or_create(
                code=code,
                defaults={
                    'name_en': name_en,
                    'name_ar': name_ar,
                    'facility_type': Facility.FacilityType.FUEL_STATION,
                    'sector': Facility.Sector.OIL_GAS,
                    'governorate': governorate,
                    'latitude': latitude,
                    'longitude': longitude,
                    'status': Facility.Status.ACTIVE,
                },
            )
            if code == 'homs-fuel-station':
                inventory_facility = station
        self._inventory_facility = inventory_facility or Facility.objects.filter(
            facility_type=Facility.FacilityType.FUEL_STATION,
        ).first()
        power_plant, _ = Facility.objects.update_or_create(
            code='national-grid',
            defaults={
                'name_en': 'National Grid',
                'name_ar': 'الشبكة الوطنية',
                'facility_type': Facility.FacilityType.POWER_PLANT,
                'sector': Facility.Sector.ELECTRICITY,
                'governorate': 'Damascus',
                'location': 'Damascus',
                'latitude': Decimal('33.520000'),
                'longitude': Decimal('36.300000'),
                'status': Facility.Status.ACTIVE,
            },
        )
        self._power_plant = power_plant
        return fields

    def _seed_map_geojson_features(self) -> None:
        """Seed map master data extracted from operational GeoJSON (fields, wells)."""
        map_fields = [
            {
                'code': 'OMAR',
                'name_ar': 'حقل العمر النفطي',
                'name_en': 'Al-Omar Oil Field',
                'governorate': 'Deir ez-Zor',
                'latitude': Decimal('35.074600'),
                'longitude': Decimal('40.601400'),
                'status': Field.Status.ACTIVE,
                'notes': 'أكبر حقول النفط في سوريا ومركز الإنتاج الرئيسي.',
            },
            {
                'code': 'RMEILAN',
                'name_ar': 'تجمع حقول الرميلان',
                'name_en': 'Rmeilan Fields Complex',
                'governorate': 'Hasakah',
                'latitude': Decimal('36.983300'),
                'longitude': Decimal('42.183300'),
                'status': Field.Status.ACTIVE,
                'notes': 'أكبر تجمع للآبار في شمال شرق سوريا، يضم أكثر من 1300 بئر.',
            },
            {
                'code': 'TANAK',
                'name_ar': 'حقل التنك النفطي',
                'name_en': 'Al-Tanak Oil Field',
                'governorate': 'Deir ez-Zor',
                'latitude': Decimal('35.124500'),
                'longitude': Decimal('40.871200'),
                'status': Field.Status.ACTIVE,
                'notes': 'من الحقول الكبرى لإنتاج النفط الخفيف في حوض الفرات.',
            },
            {
                'code': 'THAWRA',
                'name_ar': 'حقل الثورة النفطي',
                'name_en': 'Al-Thawra Oil Field',
                'governorate': 'Raqqa',
                'latitude': Decimal('35.723400'),
                'longitude': Decimal('38.541100'),
                'status': Field.Status.ACTIVE,
                'notes': 'أحد الحقول الاستراتيجية الواقعة جنوب غرب مدينة الرقة.',
            },
        ]
        created: dict[str, Field] = {}
        for spec in map_fields:
            field, _ = Field.objects.update_or_create(
                code=spec['code'],
                defaults={
                    'name_ar': spec['name_ar'],
                    'name_en': spec['name_en'],
                    'field_type': Field.FieldType.OIL,
                    'governorate': spec['governorate'],
                    'latitude': spec['latitude'],
                    'longitude': spec['longitude'],
                    'status': spec['status'],
                    'operator_company': 'Syrian Petroleum Company',
                    'notes': spec['notes'],
                },
            )
            created[spec['code']] = field

        well_specs = [
            {
                'field_code': 'OMAR',
                'well_code': 'AZB-123',
                'name_ar': 'بئر العزبة 123',
                'name_en': 'Al-Azba Well 123',
                'well_type': 'oil_gas',
                'status': 'active',
                'latitude': Decimal('35.431100'),
                'longitude': Decimal('40.354200'),
            },
            {
                'field_code': 'RMEILAN',
                'well_code': 'JAB-4',
                'name_ar': 'بئر الجبسة العميق 4',
                'name_en': 'Al-Jabsa Deep Well 4',
                'well_type': 'oil_gas',
                'status': 'active',
                'latitude': Decimal('36.211800'),
                'longitude': Decimal('41.121500'),
            },
        ]
        for spec in well_specs:
            field = created[spec['field_code']]
            Well.objects.update_or_create(
                field=field,
                well_code=spec['well_code'],
                defaults={
                    'name_ar': spec['name_ar'],
                    'name_en': spec['name_en'],
                    'well_type': spec['well_type'],
                    'status': spec['status'],
                    'latitude': spec['latitude'],
                    'longitude': spec['longitude'],
                },
            )

    def _seed_targets(self, anchor: date, days: int, fields: list[Field]) -> None:
        month_start = anchor.replace(day=1)
        national_monthly = [
            ('crude_oil_bbl', Decimal('900000'), 'bbl', 'National crude plan', 'خطة للنفط الخام'),
            ('natural_gas_mmscf', Decimal('4200'), 'MMscf', 'National gas plan', 'خطة للغاز'),
            ('total_export_bbl', Decimal('150000'), 'bbl', 'Export plan', 'خطة الصادرات'),
            ('export_revenue_usd', Decimal('11000000'), 'USD', 'Export revenue plan', 'خطة إيرادات التصدير'),
        ]
        for metric_key, value, unit, label_en, label_ar in national_monthly:
            OperationalTarget.objects.update_or_create(
                metric_key=metric_key,
                scope_type=OperationalTarget.ScopeType.NATIONAL,
                scope_code='',
                period_type=OperationalTarget.PeriodType.MONTHLY,
                period_start=month_start,
                defaults={
                    'target_value': value,
                    'unit': unit,
                    'label_en': label_en,
                    'label_ar': label_ar,
                },
            )

        daily_national = [
            ('crude_oil_bbl', Decimal('30000'), 'bbl/d'),
            ('natural_gas_mmscf', Decimal('140'), 'MMscf/d'),
            ('total_export_bbl', Decimal('5000'), 'bbl'),
            ('export_revenue_usd', Decimal('350000'), 'USD'),
            ('gasoline_stock_days', Decimal('7'), 'days'),
            ('gas_supply_to_power_percent', Decimal('95'), '%'),
        ]
        field_daily = {
            'FURAT': Decimal('14000'),
            'DEIR': Decimal('6500'),
            'EBLA': Decimal('4000'),
        }
        for offset in range(days - 1, -1, -1):
            d = anchor - timedelta(days=offset)
            for metric_key, value, unit in daily_national:
                OperationalTarget.objects.update_or_create(
                    metric_key=metric_key,
                    scope_type=OperationalTarget.ScopeType.NATIONAL,
                    scope_code='',
                    period_type=OperationalTarget.PeriodType.DAILY,
                    period_start=d,
                    defaults={'target_value': value, 'unit': unit},
                )
            for field in fields:
                if field.code in field_daily:
                    OperationalTarget.objects.update_or_create(
                        metric_key='crude_oil_bbl',
                        scope_type=OperationalTarget.ScopeType.FIELD,
                        scope_code=field.code,
                        period_type=OperationalTarget.PeriodType.DAILY,
                        period_start=d,
                        defaults={
                            'target_value': field_daily[field.code],
                            'unit': 'bbl/d',
                            'label_en': f'{field.name_en} plan',
                            'label_ar': f'خطة {field.name_ar}',
                        },
                    )

        self.stdout.write(self.style.SUCCESS('Operational targets seeded.'))

    def _seed_day(self, d: date, day_index: int, fields: list[Field]) -> None:
        # Field production aligned with ministry table (~29,417 bbl/d on anchor day)
        production_split = [13011, 0, 6130, 3845]
        for field, bbl in zip(fields, production_split, strict=True):
            if field.status == Field.Status.SHUTDOWN:
                bbl = 0
            DailyProduction.objects.update_or_create(
                field=field,
                production_date=d,
                defaults={
                    'crude_oil_bbl': Decimal(max(bbl - day_index * 40, 0)),
                    'natural_gas_mmscf': Decimal(12 + day_index * 0.2),
                    'condensate_bbl': Decimal(2446 // len(fields)),
                    'operating_hours': Decimal(24 if bbl else 0),
                },
            )

        if day_index == 0:
            ProductionLoss.objects.update_or_create(
                field=fields[1],
                loss_date=d,
                loss_type='shutdown',
                defaults={
                    'estimated_loss_bbl': Decimal('500'),
                    'reason': 'Scheduled maintenance',
                    'severity': 'critical',
                },
            )

        homs = Refinery.objects.get(refinery_name='Homs Refinery')
        banias = Refinery.objects.get(refinery_name='Banias Refinery')
        RefineryDailyOutput.objects.update_or_create(
            refinery=homs,
            production_date=d,
            defaults={
                'gasoline_ton': Decimal(4200 - day_index * 20),
                'diesel_ton': Decimal(3100),
                'fuel_oil_ton': Decimal(2800),
                'lpg_ton': Decimal(400),
            },
        )
        RefineryDailyOutput.objects.update_or_create(
            refinery=banias,
            production_date=d,
            defaults={
                'gasoline_ton': Decimal(0),
                'diesel_ton': Decimal(0),
                'fuel_oil_ton': Decimal(0),
                'lpg_ton': Decimal(0),
            },
        )

        FuelInventory.objects.update_or_create(
            facility=self._inventory_facility,
            inventory_date=d,
            fuel_type='gasoline',
            defaults={
                'current_volume': Decimal(1600 - day_index * 15),
                'max_capacity': Decimal('12000'),
            },
        )
        FuelInventory.objects.update_or_create(
            facility=self._inventory_facility,
            inventory_date=d,
            fuel_type='diesel',
            defaults={
                'current_volume': Decimal(2200),
                'max_capacity': Decimal('10000'),
            },
        )

        PowerGasSupply.objects.update_or_create(
            supply_date=d,
            facility=self._power_plant,
            defaults={'supplied_mmscf': Decimal(88 - day_index)},
        )
        PowerGasRequirement.objects.update_or_create(
            facility=self._power_plant,
            requirement_date=d,
            defaults={'required_mmscf': Decimal(100)},
        )

        Export.objects.update_or_create(
            export_date=d,
            destination_country='Mediterranean spot',
            defaults={
                'crude_bbl': Decimal(4200 + day_index * 50),
                'revenue_usd': Decimal(320000 + day_index * 8000),
            },
        )

        report, _ = DailyReport.objects.update_or_create(
            report_date=d,
            defaults={'status': DailyReport.Status.PUBLISHED},
        )
        upsert_metric(report, 'product_gasoline_t', 4200 - day_index * 20, 'homs', 't')
        upsert_metric(report, 'product_gasoline_t', 0, 'banias', 't')
        upsert_metric(report, 'product_mazut_t', 1800, 'banias', 't')
        upsert_metric(report, 'product_fuel_oil_t', 900, 'banias', 't')
        upsert_metric(report, 'dist_tonnes', 1200, 'damascus', 't')
        upsert_metric(report, 'dist_tonnes', 980, 'homs', 't')
        upsert_metric(report, 'dist_tonnes', 760, 'aleppo', 't')
