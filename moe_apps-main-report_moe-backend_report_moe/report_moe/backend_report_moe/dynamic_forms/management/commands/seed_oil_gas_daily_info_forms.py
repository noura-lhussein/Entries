"""
Ensure TitleCategory «إدارة قطاع البترول» and national daily KPI Info title.

Attribute.key = metric_key (stable migrate/dashboard mapping).
Attribute.label = Arabic display name for UI/Excel.

Usage:
  python manage.py seed_oil_gas_daily_info_forms
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.form_schema import LABEL_AR_FALLBACK
from dynamic_forms.models import Attribute, Title, TitleCategory

CATEGORY_NAME = 'إدارة قطاع البترول'
CATEGORY_ORDER = 20
NATIONAL_TITLE = 'مؤشرات التقرير اليومي للنفط والغاز'
NATIONAL_CODE = 'oil_gas.national'
TITLE_ORDER = 800

FIELD_TITLE = 'تحديث إنتاج الحقول النفطية'
FIELD_CODE = 'oil_gas.field_entity'
FIELD_ORDER = 810
# (label_ar, key, type, required)
FIELD_ATTRIBUTES: list[tuple[str, str, str, bool]] = [
    ('الحقل', 'oil_field', 'oil_field', True),
    ('تاريخ الإنتاج', 'production_date', 'date', True),
    ('إنتاج النفط الخام (برميل)', 'crude_oil_bbl', 'number', False),
    ('إنتاج الغاز الطبيعي (مليون قدم مكعب)', 'natural_gas_mmscf', 'number', False),
    ('إنتاج المكثفات (برميل)', 'condensate_bbl', 'number', False),
    ('نسبة الماء (%)', 'water_cut_percent', 'number', False),
    ('ساعات التشغيل', 'operating_hours', 'number', False),
]

REFINERY_TITLE = 'تحديث إنتاج المصافي'
REFINERY_CODE = 'oil_gas.refinery_entity'
REFINERY_ORDER = 820
REFINERY_ATTRIBUTES: list[tuple[str, str, str, bool]] = [
    ('المصفاة', 'oil_refinery', 'oil_refinery', True),
    ('تاريخ الإنتاج', 'production_date', 'date', True),
    ('البنزين (طن)', 'gasoline_ton', 'number', False),
    ('المازوت (طن)', 'diesel_ton', 'number', False),
    ('زيت الوقود (طن)', 'fuel_oil_ton', 'number', False),
    ('الغاز المسال (طن)', 'lpg_ton', 'number', False),
]

# metric_key — Arabic label from LABEL_AR_FALLBACK / catalog
EXECUTIVE_METRIC_KEYS: list[str] = [
    'total_oil_production_bbl',
    'total_crude_transferred_bbl',
    'local_clean_gas_mm3',
    'clean_gas_import_azerbaijan_mm3',
    'clean_gas_import_jordan_mm3',
    'total_clean_gas_mm3',
    'clean_gas_distributed_mm3',
    'electricity_clean_gas_consumption_mm3',
    'mazut_sold_thu_fri_m3',
    'gasoline_90_95_sold_thu_fri_m3',
    'domestic_lpg_sold_m3',
    'fuel_oil_sold_m3',
    'brent_crude_price_usd_bbl',
    'gas_price_usd_mmbtu',
]


class Command(BaseCommand):
    help = 'Seed oil & gas national daily Info title under إدارة قطاع البترول.'

    @transaction.atomic
    def handle(self, *args, **options):
        category, cat_created = TitleCategory.objects.get_or_create(
            name=CATEGORY_NAME,
            defaults={'order': CATEGORY_ORDER},
        )
        self.stdout.write(
            f"Category id={category.id} {'created' if cat_created else 'exists'}: {CATEGORY_NAME}"
        )

        title, title_created = Title.objects.get_or_create(
            name=NATIONAL_TITLE,
            defaults={'order': TITLE_ORDER, 'category': category, 'code': NATIONAL_CODE, 'is_system': True},
        )
        changed = []
        if title.category_id != category.id:
            title.category = category
            changed.append('category')
        if title.order != TITLE_ORDER:
            title.order = TITLE_ORDER
            changed.append('order')
        if title.code != NATIONAL_CODE:
            title.code = NATIONAL_CODE
            changed.append('code')
        if not title.is_system:
            title.is_system = True
            changed.append('is_system')
        if changed:
            title.save(update_fields=changed)
        self.stdout.write(
            f"  Title id={title.id} {'created' if title_created else 'linked'}: {title.name} (code={NATIONAL_CODE})"
        )

        attr_created = 0
        date_attr, date_was = Attribute.objects.get_or_create(
            title=title,
            label='تاريخ التقرير',
            defaults={'type': 'date', 'required': True, 'key': 'report_date', 'is_system': True},
        )
        if date_was:
            attr_created += 1
        else:
            date_changed = []
            if not date_attr.key:
                date_attr.key = 'report_date'
                date_changed.append('key')
            if not date_attr.is_system:
                date_attr.is_system = True
                date_changed.append('is_system')
            if date_changed:
                date_attr.save(update_fields=date_changed)

        for order, key in enumerate(EXECUTIVE_METRIC_KEYS, start=1):
            label_ar = LABEL_AR_FALLBACK.get(key, key)
            attr = (
                Attribute.objects.filter(title=title, key=key).first()
                or Attribute.objects.filter(title=title, label=key).first()
                or Attribute.objects.filter(title=title, label=label_ar).first()
            )
            if attr:
                changed = []
                if attr.label != label_ar:
                    attr.label = label_ar
                    changed.append('label')
                if attr.key != key:
                    attr.key = key
                    changed.append('key')
                if not attr.is_measure:
                    attr.is_measure = True
                    changed.append('is_measure')
                if attr.measure_order != order:
                    attr.measure_order = order
                    changed.append('measure_order')
                if not attr.is_system:
                    attr.is_system = True
                    changed.append('is_system')
                if changed:
                    attr.save(update_fields=changed)
            else:
                Attribute.objects.create(
                    title=title,
                    label=label_ar,
                    type='number',
                    required=False,
                    key=key,
                    is_measure=True,
                    measure_order=order,
                    is_system=True,
                )
                attr_created += 1

        for entity_title, entity_code, entity_order, entity_attrs in (
            (FIELD_TITLE, FIELD_CODE, FIELD_ORDER, FIELD_ATTRIBUTES),
            (REFINERY_TITLE, REFINERY_CODE, REFINERY_ORDER, REFINERY_ATTRIBUTES),
        ):
            attr_created += self._seed_entity_title(
                category, entity_title, entity_code, entity_order, entity_attrs,
            )

        self.stdout.write(self.style.SUCCESS(f'Done. New attributes: {attr_created}.'))

    def _seed_entity_title(
        self,
        category: TitleCategory,
        title_name: str,
        title_code: str,
        order: int,
        attributes: list[tuple[str, str, str, bool]],
    ) -> int:
        title = Title.objects.filter(code=title_code).first() or Title.objects.filter(
            name=title_name
        ).first()
        created_title = title is None
        if title is None:
            title = Title.objects.create(
                name=title_name, code=title_code, order=order, category=category, is_system=True,
            )
        changed = []
        if title.code != title_code:
            title.code = title_code
            changed.append('code')
        if title.category_id != category.id:
            title.category = category
            changed.append('category')
        if not title.is_system:
            title.is_system = True
            changed.append('is_system')
        if changed:
            title.save(update_fields=changed)
        self.stdout.write(
            f"  Title id={title.id} {'created' if created_title else 'linked'}: "
            f"{title.name} (code={title_code})"
        )

        existing_by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
        existing_by_label = {a.label: a for a in Attribute.objects.filter(title=title)}
        created = 0
        for attr_order, (label, key, attr_type, required) in enumerate(attributes):
            attr = existing_by_key.get(key) or existing_by_label.get(label)
            if attr is None:
                Attribute.objects.create(
                    title=title,
                    label=label,
                    key=key,
                    type=attr_type,
                    required=required,
                    order=attr_order,
                    is_system=True,
                )
                created += 1
                self.stdout.write(f"    + attribute key={key} type={attr_type}")
                continue
            update_fields = []
            if attr.key != key:
                attr.key = key
                update_fields.append('key')
            if not attr.is_system:
                attr.is_system = True
                update_fields.append('is_system')
            if update_fields:
                attr.save(update_fields=update_fields)
                self.stdout.write(f"    ~ attribute key={key} updated({','.join(update_fields)})")
        return created
