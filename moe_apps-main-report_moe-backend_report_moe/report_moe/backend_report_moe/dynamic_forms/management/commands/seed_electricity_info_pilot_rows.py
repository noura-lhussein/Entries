"""
Create sample accepted Info rows for electricity portal Info-only surfaces.

Requires:
  - Titles from seed_energy_entity_pilot_forms / seed_remaining_entity_pilot_forms
  - At least one PowerPlant / Substation row in schema `moeds`

Usage:
  python manage.py seed_energy_entity_pilot_forms
  python manage.py seed_remaining_entity_pilot_forms
  python manage.py seed_electricity_info_pilot_rows
"""

from __future__ import annotations

import uuid
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title


def _attr(title: Title, label: str) -> Attribute | None:
    return Attribute.objects.filter(title=title, label=label).first()


class Command(BaseCommand):
    help = 'Seed accepted electricity Info pilot rows linked to moeds masters.'

    @transaction.atomic
    def handle(self, *args, **options):
        from master_data.models import (
            PowerPlant,
            Substation,
        )

        plant = PowerPlant.objects.order_by('id').first()
        sub = Substation.objects.order_by('id').first()
        if plant is None and sub is None:
            self.stderr.write(
                self.style.ERROR(
                    'No power plant / substation rows found. '
                    'Populate moeds electricity masters first.'
                )
            )
            return

        leaf = (
            SubMainSection.objects.filter(parent__isnull=False)
            .order_by('id')
            .first()
        ) or SubMainSection.objects.order_by('id').first()
        if leaf is None:
            self.stderr.write(self.style.ERROR('No SubMainSection available.'))
            return

        created = 0
        today = date.today().isoformat()

        gen_title = Title.objects.filter(name='تحديث توليد محطات الكهرباء').first()
        if gen_title and plant is not None:
            row_key = uuid.uuid4()
            pairs = [
                ('محطة التوليد', str(plant.id), 'power_plant', plant.id),
                ('تاريخ التقرير', today, None, None),
                ('التوليد (ميجاواط ساعة)', '1250.5', None, None),
                ('ملاحظات', 'seed_electricity_info_pilot_rows', None, None),
            ]
            for label, value, entity_type, entity_id in pairs:
                attr = _attr(gen_title, label)
                if attr is None:
                    continue
                _, was_created = Info.objects.get_or_create(
                    attribute=attr,
                    sub_main=leaf,
                    row_key=row_key,
                    defaults={
                        'value': value,
                        'confirmed': Info.ConfirmStatus.ACCEPT,
                        'entity_type': entity_type or '',
                        'entity_id': entity_id,
                    },
                )
                if was_created:
                    created += 1
            self.stdout.write(
                f'Plant Info: plant_id={plant.id} title={gen_title.id} row_key={row_key}'
            )

        sub_title = Title.objects.filter(name='تحديث حالة محطات التحويل').first()
        if sub_title and sub is not None:
            row_key = uuid.uuid4()
            pairs = [
                ('محطة التحويل', str(sub.id), 'substation', sub.id),
                ('تاريخ التحديث', today, None, None),
                ('هل المحطة عاملة؟', 'true', None, None),
                ('ملاحظات', 'seed_electricity_info_pilot_rows', None, None),
            ]
            for label, value, entity_type, entity_id in pairs:
                attr = _attr(sub_title, label)
                if attr is None:
                    continue
                _, was_created = Info.objects.get_or_create(
                    attribute=attr,
                    sub_main=leaf,
                    row_key=row_key,
                    defaults={
                        'value': value,
                        'confirmed': Info.ConfirmStatus.ACCEPT,
                        'entity_type': entity_type or '',
                        'entity_id': entity_id,
                    },
                )
                if was_created:
                    created += 1
            self.stdout.write(
                f'Substation Info: substation_id={sub.id} title={sub_title.id} row_key={row_key}'
            )

        if created == 0 and (gen_title is None or sub_title is None):
            self.stderr.write(
                self.style.WARNING(
                    'Pilot titles missing. Run seed_energy_entity_pilot_forms first.'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. New Info rows: {created}. '
                'Verify moeds Data / Map / Dashboard for sector=electricity.'
            )
        )
