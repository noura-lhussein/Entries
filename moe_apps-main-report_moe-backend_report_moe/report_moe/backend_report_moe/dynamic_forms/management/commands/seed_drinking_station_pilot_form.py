"""
Seed the drinking-station assessment Title + Attributes (schema-contract compliant).

Creates/updates (idempotent by title code / attribute key):
  Title: code='water.drinking_station_entity' (label: "تحديث محطات مياه الشرب")
  Attributes: entity link + assessment date + ~31 station-condition fields,
  each with a stable `key` (never matched by `.label` or `.type`).

These are periodic station-assessment fields (operational status, equipment
condition, power source, safety), not daily time-series readings — a station
gets re-assessed occasionally, not once a day. Fixed identity/location fields
(name, coordinates, station code) live in master_data, not here.

Usage:
  python manage.py seed_drinking_station_pilot_form
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Title, TitleCategory

TITLE_NAME = 'تحديث محطات مياه الشرب'
TITLE_CODE = 'water.drinking_station_entity'
CATEGORY_NAME = 'إدارة قطاع المياه'

# (label_ar, key, type, required)
ATTRIBUTES = [
    ('محطة مياه الشرب', 'drinking_station', 'drinking_station', True),
    ('تاريخ التقييم', 'assessment_date', 'date', True),
    ('هل المحطة عاملة؟', 'is_operational', 'boolean', False),
    ('سبب التعطل', 'non_operational_reason', 'text', False),
    ('محطة رفع؟', 'is_boosting_station', 'boolean', False),
    ('محطة بئر؟', 'is_well_station', 'boolean', False),
    ('محطة ترشيح؟', 'is_filtration_station', 'boolean', False),
    ('بحاجة لطاقة شمسية؟', 'needs_solar_power', 'boolean', False),
    ('متصلة بالشبكة العامة؟', 'has_grid_power', 'boolean', False),
    ('حالة المبنى', 'building_condition', 'select', False),
    ('إجراءات السلامة', 'safety_procedures', 'select', False),
    ('تم تأهيلها سابقاً؟', 'previously_rehabilitated', 'boolean', False),
    ('نوع التأهيل', 'rehabilitation_type', 'select', False),
    ('يوجد حماية من المطرقة المائية؟', 'has_water_hammer_protection', 'boolean', False),
    ('كفاءة حماية المطرقة المائية', 'water_hammer_efficiency', 'select', False),
    ('يوجد تغذية من الشبكة العامة؟', 'has_public_grid_supply', 'boolean', False),
    ('الربط الكهربائي يعمل؟', 'grid_connection_working', 'boolean', False),
    ('كفاءة الربط الكهربائي', 'electrical_connection_efficiency', 'select', False),
    ('كفاءة اللوحة الكهربائية', 'electrical_panel_efficiency', 'select', False),
    ('كفاءة المحول', 'transformer_efficiency', 'select', False),
    ('تتوفر طاقة شمسية؟', 'solar_power_available', 'boolean', False),
    ('كفاءة المنظومة الشمسية', 'solar_system_efficiency', 'select', False),
    ('بحاجة لتركيب منظومة شمسية؟', 'needs_solar_installation', 'boolean', False),
    ('يتوفر مولد؟', 'generator_available', 'boolean', False),
    ('يوجد مصدر طاقة بديل؟', 'alternative_power_source', 'boolean', False),
    ('تتوفر مساحة لمنظومة شمسية؟', 'solar_space_available', 'boolean', False),
    ('إنتاجية الشبكة العامة', 'grid_power_productivity', 'select', False),
    ('إنتاجية الطاقة الشمسية', 'solar_power_productivity', 'select', False),
    ('تم تحليل المياه؟', 'is_water_analyzed', 'boolean', False),
    ('حالة معدات المختبر', 'lab_equipment_status', 'select', False),
    ('يوجد خزانات مياه؟', 'has_water_tanks', 'boolean', False),
    ('ملاحظات', 'notes', 'textarea', False),
]


class Command(BaseCommand):
    help = 'Seed Form Builder title/attributes for drinking-station assessments.'

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = TitleCategory.objects.get_or_create(
            name=CATEGORY_NAME,
            defaults={'order': 30},
        )
        title = Title.objects.filter(code=TITLE_CODE).first() or Title.objects.filter(
            name=TITLE_NAME
        ).first()
        created = title is None
        if title is None:
            title = Title.objects.create(
                name=TITLE_NAME, code=TITLE_CODE, order=900, category=category, is_system=True,
            )
        changed_fields = []
        if title.code != TITLE_CODE:
            title.code = TITLE_CODE
            changed_fields.append('code')
        if title.category_id != category.id:
            title.category = category
            changed_fields.append('category')
        if not title.is_system:
            title.is_system = True
            changed_fields.append('is_system')
        if changed_fields:
            title.save(update_fields=changed_fields)
        self.stdout.write(
            f"Title id={title.id} code={title.code} {'created' if created else 'exists'}"
        )

        existing_by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
        existing_by_label = {a.label: a for a in Attribute.objects.filter(title=title)}

        created_attrs = 0
        for order, (label, key, attr_type, required) in enumerate(ATTRIBUTES):
            attr = existing_by_key.get(key) or existing_by_label.get(label)
            if attr is None:
                Attribute.objects.create(
                    title=title,
                    label=label,
                    key=key,
                    type=attr_type,
                    required=required,
                    order=order,
                    is_system=True,
                )
                created_attrs += 1
                self.stdout.write(f"  + attribute key={key} type={attr_type}")
                continue
            update_fields = []
            if attr.key != key:
                attr.key = key
                update_fields.append('key')
            if not attr.is_system:
                attr.is_system = True
                update_fields.append('is_system')
            if attr.order != order:
                attr.order = order
                update_fields.append('order')
            if update_fields:
                attr.save(update_fields=update_fields)
                self.stdout.write(f"  ~ attribute key={key} updated({','.join(update_fields)})")
            else:
                self.stdout.write(f"  = attribute key={key} exists")

        self.stdout.write(self.style.SUCCESS(
            f'Done. New attributes: {created_attrs}. '
            'Assign this title + a leaf sub-section to a user to enter data.'
        ))
