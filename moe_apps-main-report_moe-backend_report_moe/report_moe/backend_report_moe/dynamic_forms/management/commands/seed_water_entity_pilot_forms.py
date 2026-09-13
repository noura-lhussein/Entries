"""
Seed pilot Titles + Attributes for dam and rainfall station updates.

Idempotent by title name.

Usage:
  python manage.py seed_water_entity_pilot_forms
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Title

# (label_ar, label_en, attr_type, required, key, is_measure) — `key` is the stable
# identifier moeds' info_dashboard.py reads by; label_ar/label_en/order stay free
# to edit from the report_moe UI without breaking anything downstream.
PILOTS = [
    {
        'title': 'تحديث تخزين السدود',
        'code': 'water.dam_entity',
        'order': 901,
        'attributes': [
            ('السد', 'Dam', 'dam', True, 'dam', False),
            ('تاريخ القراءة', 'Reading date', 'date', True, 'reading_date', False),
            ('التخزين (مليون م3)', 'Storage (M m³)', 'number', True, 'storage_mcm', True),
            ('ملاحظات', 'Notes', 'textarea', False, 'notes', False),
        ],
    },
    {
        'title': 'تحديث رصد الهطول',
        'code': 'water.rainfall_entity',
        'order': 902,
        'attributes': [
            ('محطة الهطول', 'Rainfall station', 'rainfall_station', True, 'station', False),
            ('تاريخ الرصد', 'Observation date', 'date', True, 'observation_date', False),
            ('الهطول (مم)', 'Precipitation (mm)', 'number', True, 'precipitation_mm', True),
            ('ملاحظات', 'Notes', 'textarea', False, 'notes', False),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed pilot Form Builder titles for dam storage and rainfall observations.'

    @transaction.atomic
    def handle(self, *args, **options):
        total_new = 0
        for pilot in PILOTS:
            title, created = Title.objects.get_or_create(
                name=pilot['title'],
                defaults={'order': pilot['order'], 'code': pilot['code'], 'is_system': True},
            )
            title_changed = []
            if title.code != pilot['code']:
                title.code = pilot['code']
                title_changed.append('code')
            if not title.is_system:
                title.is_system = True
                title_changed.append('is_system')
            if title_changed:
                title.save(update_fields=title_changed)
            self.stdout.write(
                f"Title id={title.id} {'created' if created else 'exists'} (code={pilot['code']})"
            )
            for label_ar, label_en, attr_type, required, key, is_measure in pilot['attributes']:
                attr = Attribute.objects.filter(title=title, key=key).first()
                if attr is None:
                    # Back-compat: earlier runs of this command created attributes
                    # with no key at all, matched only by label — pick those up
                    # instead of creating a duplicate row.
                    attr = Attribute.objects.filter(title=title, label=label_ar, key='').first()

                if attr is None:
                    Attribute.objects.create(
                        title=title,
                        label=label_ar,
                        label_en=label_en,
                        type=attr_type,
                        required=required,
                        key=key,
                        is_measure=is_measure,
                        is_system=True,
                    )
                    total_new += 1
                    self.stdout.write(f"  + attribute type={attr_type} key={key}")
                else:
                    changed = []
                    if attr.key != key:
                        attr.key = key
                        changed.append('key')
                    if attr.label_en != label_en:
                        attr.label_en = label_en
                        changed.append('label_en')
                    if attr.is_measure != is_measure:
                        attr.is_measure = is_measure
                        changed.append('is_measure')
                    if not attr.is_system:
                        attr.is_system = True
                        changed.append('is_system')
                    if changed:
                        attr.save(update_fields=changed)
                    self.stdout.write(f"  = attribute exists type={attr_type} key={key}")

        self.stdout.write(self.style.SUCCESS(
            f'Done. New attributes: {total_new}. '
            'Assign each title + a leaf sub-section to a user to enter data.'
        ))
