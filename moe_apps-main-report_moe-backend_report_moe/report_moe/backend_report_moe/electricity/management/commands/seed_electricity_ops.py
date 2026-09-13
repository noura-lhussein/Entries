from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from electricity.alert_engine import evaluate_alerts
from electricity.models import (
    DailyDemand,
    DailyGeneration,
    DailyReport,
    OperationalTarget,
    PowerPlant,
    Substation,
    TransmissionLine,
)
from electricity.snapshot_builder import build_kpi_snapshot


class Command(BaseCommand):
    help = 'Seed electricity operational data, KPI snapshots, and alerts.'

    def add_arguments(self, parser):
        parser.add_argument('--anchor-date', default='2026-03-25')
        parser.add_argument('--days', type=int, default=14)

    @transaction.atomic
    def handle(self, *args, **options):
        anchor = date.fromisoformat(options['anchor_date'])
        days = options['days']
        plants = self._seed_master_data()
        self._seed_targets(anchor, plants)
        self.stdout.write(self.style.SUCCESS(f'Master data ready ({len(plants)} plants).'))

        for offset in range(days - 1, -1, -1):
            d = anchor - timedelta(days=offset)
            day_index = days - 1 - offset
            self._seed_day(d, day_index, plants)
            snapshot = build_kpi_snapshot(d)
            alert_count = evaluate_alerts(d, snapshot)
            snapshot.active_alerts_count = alert_count
            snapshot.save(update_fields=['active_alerts_count'])
            DailyReport.objects.update_or_create(
                report_date=d,
                defaults={'status': DailyReport.Status.PUBLISHED},
            )

        self.stdout.write(self.style.SUCCESS(f'Seeded {days} days ending {anchor}.'))

    def _seed_master_data(self) -> list[PowerPlant]:
        specs = [
            ('ZAYZOUN', 'محطة الزيزون', 'Al-Zayzoun Thermal', PowerPlant.PlantType.THERMAL, PowerPlant.FuelType.GAS, 600, Decimal('32.950000'), Decimal('35.880000'), 'Quneitra'),
            ('TISHREEN', 'سد تشرين', 'Tishreen Hydro', PowerPlant.PlantType.HYDRO, PowerPlant.FuelType.NONE, 630, Decimal('35.970000'), Decimal('38.450000'), 'Raqqa'),
            ('DEIR-ALI', 'دير علي', 'Deir Ali Thermal', PowerPlant.PlantType.THERMAL, PowerPlant.FuelType.DUAL, 750, Decimal('33.480000'), Decimal('36.120000'), 'Damascus'),
            ('PALMYRA', 'تدمر الشمسية', 'Palmyra Solar', PowerPlant.PlantType.SOLAR, PowerPlant.FuelType.NONE, 50, Decimal('34.550000'), Decimal('38.270000'), 'Homs'),
        ]
        plants = []
        for code, ar, en, ptype, fuel, mw, lat, lng, governorate in specs:
            plant, _ = PowerPlant.objects.update_or_create(
                code=code,
                defaults={
                    'name_ar': ar,
                    'name_en': en,
                    'plant_type': ptype,
                    'fuel_type': fuel,
                    'governorate': governorate,
                    'latitude': lat,
                    'longitude': lng,
                    'status': PowerPlant.Status.ACTIVE,
                    'installed_capacity_mw': Decimal(mw),
                    'operator_company': 'Public Establishment for Generation',
                },
            )
            plants.append(plant)

        Substation.objects.update_or_create(
            code='DAM-400',
            defaults={
                'name_ar': 'محطة دمشق 400',
                'name_en': 'Damascus 400 kV',
                'role': Substation.Role.TRANSMISSION,
                'voltage_kv': Decimal('400'),
                'governorate': 'Damascus',
                'latitude': Decimal('33.513800'),
                'longitude': Decimal('36.276500'),
                'status': Substation.Status.ACTIVE,
            },
        )
        Substation.objects.update_or_create(
            code='HOMS-230',
            defaults={
                'name_ar': 'محطة حمص 230',
                'name_en': 'Homs 230 kV',
                'role': Substation.Role.TRANSMISSION,
                'voltage_kv': Decimal('230'),
                'governorate': 'Homs',
                'latitude': Decimal('34.731900'),
                'longitude': Decimal('36.709800'),
                'status': Substation.Status.ACTIVE,
            },
        )
        TransmissionLine.objects.update_or_create(
            name='Damascus–Homs 400 kV',
            defaults={
                'source_location': 'Damascus',
                'destination_location': 'Homs',
                'source_latitude': Decimal('33.513800'),
                'source_longitude': Decimal('36.276500'),
                'dest_latitude': Decimal('34.731900'),
                'dest_longitude': Decimal('36.709800'),
                'length_km': Decimal('165'),
                'capacity_mw': Decimal('800'),
                'voltage_kv': Decimal('400'),
                'status': TransmissionLine.Status.NORMAL,
            },
        )
        return plants

    def _seed_targets(self, anchor: date, plants: list[PowerPlant]) -> None:
        targets = [
            ('total_generation_mwh', OperationalTarget.ScopeType.NATIONAL, '', Decimal('8500')),
            ('peak_demand_mw', OperationalTarget.ScopeType.NATIONAL, '', Decimal('3200')),
            ('plant_availability_percent', OperationalTarget.ScopeType.NATIONAL, '', Decimal('85')),
        ]
        for key, scope, code, val in targets:
            OperationalTarget.objects.update_or_create(
                metric_key=key,
                scope_type=scope,
                scope_code=code,
                period_type=OperationalTarget.PeriodType.DAILY,
                period_start=anchor,
                defaults={'target_value': val, 'unit': ''},
            )
        for plant in plants:
            OperationalTarget.objects.update_or_create(
                metric_key='generation_mwh',
                scope_type=OperationalTarget.ScopeType.PLANT,
                scope_code=plant.code,
                period_type=OperationalTarget.PeriodType.DAILY,
                period_start=anchor,
                defaults={
                    'target_value': (plant.installed_capacity_mw or Decimal('100')) * Decimal('12'),
                    'unit': 'MWh/d',
                },
            )

    def _seed_day(self, d: date, day_index: int, plants: list[PowerPlant]) -> None:
        factor = Decimal('0.85') + Decimal(str((day_index % 5) * 0.02))
        total_peak = Decimal('0')
        for i, plant in enumerate(plants):
            cap = plant.installed_capacity_mw or Decimal('100')
            gen_mwh = cap * Decimal('18') * factor * (Decimal('1') - Decimal(str(i * 0.05)))
            peak = cap * factor * Decimal('0.9')
            total_peak += peak
            DailyGeneration.objects.update_or_create(
                plant=plant,
                report_date=d,
                defaults={
                    'gross_generation_mwh': gen_mwh.quantize(Decimal('0.01')),
                    'peak_mw': peak.quantize(Decimal('0.01')),
                    'available_capacity_mw': cap * factor,
                    'forced_outage_mw': Decimal('0') if i < 3 else cap * Decimal('0.1'),
                },
            )

        DailyDemand.objects.update_or_create(
            report_date=d,
            defaults={
                'peak_demand_mw': (total_peak * Decimal('1.05')).quantize(Decimal('0.01')),
                'energy_consumed_mwh': (total_peak * Decimal('20')).quantize(Decimal('0.01')),
            },

        )
