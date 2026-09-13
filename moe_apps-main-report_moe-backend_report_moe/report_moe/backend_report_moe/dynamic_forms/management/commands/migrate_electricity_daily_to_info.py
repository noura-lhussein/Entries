"""
Migrate published moeds electricity DailyReport rows into accepted Info.

Prereqs:
  python manage.py seed_electricity_daily_info_forms
  (moeds) python manage.py seed_electricity_daily_catalogs
  (moeds) migrate 0011 catalogs

Usage:
  python manage.py migrate_electricity_daily_to_info --sub-main-id 15
  python manage.py migrate_electricity_daily_to_info --sub-main-id 15 --apply
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from master_data.models import (
    FuelTankStation,
    HydroDam,
    LoadGovernorate,
    PowerPlant,
)

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[electricity-daily-migration]'

TITLE_NATIONAL = 'مؤشرات التقرير اليومي للكهرباء'
TITLE_UNITS = 'تحديث توليد وحدات المحطات'
TITLE_FUEL = 'تحديث خزانات الوقود'
TITLE_GOV = 'تحديث أحمال المحافظات'
TITLE_HYDRO = 'تحديث قراءات السدود'
TITLE_INC_GEN = 'تسجيل حوادث التوليد'
TITLE_INC_GRID = 'تسجيل حوادث الخطوط'
TITLE_NOTES = 'صيانة وملاحظات يومية'


def _attrs(title_name: str) -> tuple[Title, dict[str, Attribute]]:
    title = Title.objects.filter(name=title_name).first()
    if title is None:
        raise CommandError(f'Title missing: {title_name}. Run seed_electricity_daily_info_forms.')
    by_label = {a.label: a for a in Attribute.objects.filter(title=title)}
    return title, by_label


def _create_info(
    *,
    attribute: Attribute,
    sub_main: SubMainSection,
    row_key: uuid.UUID,
    value: str,
    entity_type: str = '',
    entity_id: int | None = None,
) -> bool:
    # Matches the DB's real UniqueConstraint scope — (attribute, row_key) only,
    # not sub_main. Earlier runs of this command used different --sub-main-id
    # values per title, so a sub_main-scoped check here would miss real
    # duplicates and crash on the DB constraint instead of skipping cleanly.
    exists = Info.objects.filter(
        attribute=attribute,
        row_key=row_key,
    ).exists()
    if exists:
        return False
    Info.objects.create(
        attribute=attribute,
        sub_main=sub_main,
        row_key=row_key,
        value=value,
        confirmed=Info.ConfirmStatus.ACCEPT,
        entity_type=entity_type or '',
        entity_id=entity_id,
        commit_note=NOTE_TAG,
    )
    return True


class Command(BaseCommand):
    help = 'Migrate published electricity DailyReport data into Info (default dry-run).'

    def add_arguments(self, parser):
        parser.add_argument('--sub-main-id', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--limit-dates', type=int, default=0, help='0 = all published dates')

    def handle(self, *args, **options):
        sub = SubMainSection.objects.filter(pk=options['sub_main_id']).first()
        if sub is None:
            raise CommandError(f'SubMainSection {options["sub_main_id"]} not found.')

        apply = bool(options['apply'])
        limit = int(options['limit_dates'] or 0)

        plant_by_code = {p.code: p.id for p in PowerPlant.objects.all()}
        tank_by_code = {t.code: t.id for t in FuelTankStation.objects.all()}
        dam_by_code = {d.code: d.id for d in HydroDam.objects.all()}
        gov_by_code = {g.code: g.id for g in LoadGovernorate.objects.all()}

        if not tank_by_code or not gov_by_code or not dam_by_code:
            self.stderr.write(
                self.style.WARNING(
                    'Catalog tables empty or partial. '
                    'Run moeds: seed_electricity_daily_catalogs (+ migrate 0011).'
                )
            )

        _, nat_attrs = _attrs(TITLE_NATIONAL)
        _, unit_attrs = _attrs(TITLE_UNITS)
        _, fuel_attrs = _attrs(TITLE_FUEL)
        _, gov_attrs = _attrs(TITLE_GOV)
        _, hydro_attrs = _attrs(TITLE_HYDRO)
        _, inc_g_attrs = _attrs(TITLE_INC_GEN)
        _, inc_l_attrs = _attrs(TITLE_INC_GRID)
        _, note_attrs = _attrs(TITLE_NOTES)

        reports = self._fetch_reports(limit)
        created = 0
        skipped = 0

        for report in reports:
            report_id = int(report['id'])
            report_date: date = report['report_date']
            date_s = report_date.isoformat()
            self.stdout.write(f'--- {date_s} (report_id={report_id}) ---')

            def write_batch(fn):
                nonlocal created, skipped
                if apply:
                    with transaction.atomic():
                        c, s = fn()
                else:
                    c, s = fn()
                created += c
                skipped += s

            write_batch(
                lambda: self._migrate_national(
                    sub, nat_attrs, report_id, date_s, apply
                )
            )
            write_batch(
                lambda: self._migrate_units(
                    sub, unit_attrs, report_id, date_s, plant_by_code, apply
                )
            )
            write_batch(
                lambda: self._migrate_fuel(
                    sub, fuel_attrs, report_id, date_s, tank_by_code, apply
                )
            )
            write_batch(
                lambda: self._migrate_gov(
                    sub, gov_attrs, report_id, date_s, gov_by_code, apply
                )
            )
            write_batch(
                lambda: self._migrate_hydro(
                    sub, hydro_attrs, report_id, date_s, dam_by_code, apply
                )
            )
            write_batch(
                lambda: self._migrate_inc_gen(sub, inc_g_attrs, report_id, date_s, apply)
            )
            write_batch(
                lambda: self._migrate_inc_grid(sub, inc_l_attrs, report_id, date_s, apply)
            )
            write_batch(
                lambda: self._migrate_notes(sub, note_attrs, report, date_s, apply)
            )

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(self.style.SUCCESS(f'{mode}: created≈{created}, skipped≈{skipped}'))

    def _fetch_reports(self, limit: int) -> list[dict[str, Any]]:
        sql = """
            SELECT id, report_date, reference_hour, peak_generation_time,
                   notes_ar, notes_en, maintenance_groups_ar
            FROM electricity_dailyreport
            WHERE status = 'published'
            ORDER BY report_date DESC
        """
        if limit > 0:
            sql += f' LIMIT {int(limit)}'
        with connections['default'].cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _migrate_national(self, sub, attrs, report_id, date_s, apply):
        created = skipped = 0
        date_attr = attrs.get('تاريخ التقرير')
        if date_attr is None:
            return 0, 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                'SELECT metric_key, value FROM electricity_dailymetric WHERE report_id = %s',
                [report_id],
            )
            metrics = list(cursor.fetchall())
        if not metrics and not apply:
            return 0, 0
        row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'el-national-{date_s}')
        if apply:
            if _create_info(
                attribute=date_attr, sub_main=sub, row_key=row_key, value=date_s
            ):
                created += 1
            else:
                skipped += 1
            for key, value in metrics:
                attr = attrs.get(str(key))
                if attr is None:
                    continue
                if _create_info(
                    attribute=attr,
                    sub_main=sub,
                    row_key=row_key,
                    value=str(value),
                ):
                    created += 1
                else:
                    skipped += 1
        else:
            created += 1 + len([k for k, _ in metrics if str(k) in attrs])
        return created, skipped

    def _migrate_units(self, sub, attrs, report_id, date_s, plant_by_code, apply):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT plant_code, unit_code, nominal_mw, available_mw,
                       generation_mwh_24h, status
                FROM electricity_generationunitreading WHERE report_id = %s
                """,
                [report_id],
            )
            rows = cursor.fetchall()
        for plant_code, unit_code, nominal, available, gen, status in rows:
            plant_id = plant_by_code.get(str(plant_code))
            if plant_id is None:
                skipped += 1
                continue
            row_key = uuid.uuid5(
                uuid.NAMESPACE_URL, f'el-unit-{date_s}-{plant_code}-{unit_code or ""}'
            )
            pairs = [
                (attrs.get('محطة التوليد'), str(plant_id), 'power_plant', plant_id),
                (attrs.get('تاريخ التقرير'), date_s, 'power_plant', plant_id),
                (attrs.get('رمز الوحدة'), str(unit_code or ''), 'power_plant', plant_id),
                (
                    attrs.get('القدرة الاسمية (ميجاواط)'),
                    '' if nominal is None else str(nominal),
                    'power_plant',
                    plant_id,
                ),
                (
                    attrs.get('المتاح (ميجاواط)'),
                    '' if available is None else str(available),
                    'power_plant',
                    plant_id,
                ),
                (
                    attrs.get('التوليد 24س (ميجاواط ساعة)'),
                    '' if gen is None else str(gen),
                    'power_plant',
                    plant_id,
                ),
                (attrs.get('الحالة'), str(status or ''), 'power_plant', plant_id),
            ]
            for attr, value, et, eid in pairs:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr,
                        sub_main=sub,
                        row_key=row_key,
                        value=value,
                        entity_type=et,
                        entity_id=eid,
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_fuel(self, sub, attrs, report_id, date_s, tank_by_code, apply):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT station_code, current_tons
                FROM electricity_fueltankreading WHERE report_id = %s
                """,
                [report_id],
            )
            rows = cursor.fetchall()
        for code, current in rows:
            tank_id = tank_by_code.get(str(code))
            if tank_id is None:
                skipped += 1
                continue
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'el-fuel-{date_s}-{code}')
            pairs = [
                (attrs.get('محطة الخزان'), str(tank_id), 'fuel_tank_station', tank_id),
                (attrs.get('تاريخ القراءة'), date_s, 'fuel_tank_station', tank_id),
                (
                    attrs.get('المخزون الحالي (طن)'),
                    '' if current is None else str(current),
                    'fuel_tank_station',
                    tank_id,
                ),
            ]
            for attr, value, et, eid in pairs:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr,
                        sub_main=sub,
                        row_key=row_key,
                        value=value,
                        entity_type=et,
                        entity_id=eid,
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_gov(self, sub, attrs, report_id, date_s, gov_by_code, apply):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT governorate_code, consumed_mw, allocated_mw
                FROM electricity_governorateload WHERE report_id = %s
                """,
                [report_id],
            )
            rows = cursor.fetchall()
        for code, consumed, allocated in rows:
            gov_id = gov_by_code.get(str(code))
            if gov_id is None:
                skipped += 1
                continue
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'el-gov-{date_s}-{code}')
            pairs = [
                (attrs.get('المحافظة'), str(gov_id), 'load_governorate', gov_id),
                (attrs.get('تاريخ التقرير'), date_s, 'load_governorate', gov_id),
                (
                    attrs.get('المستهلك (ميجاواط)'),
                    '' if consumed is None else str(consumed),
                    'load_governorate',
                    gov_id,
                ),
                (
                    attrs.get('المخصّص (ميجاواط)'),
                    '' if allocated is None else str(allocated),
                    'load_governorate',
                    gov_id,
                ),
            ]
            for attr, value, et, eid in pairs:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr,
                        sub_main=sub,
                        row_key=row_key,
                        value=value,
                        entity_type=et,
                        entity_id=eid,
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_hydro(self, sub, attrs, report_id, date_s, dam_by_code, apply):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT dam_code, front_level_m, back_level_m, generation_mwh,
                       outflow_m3s, inflow_m3s, expected_m3s
                FROM electricity_hydrodamreading WHERE report_id = %s
                """,
                [report_id],
            )
            rows = cursor.fetchall()
        field_map = [
            ('المنسوب الأمامي (م)', 1),
            ('المنسوب الخلفي (م)', 2),
            ('التوليد (ميجاواط ساعة)', 3),
            ('التصريف (م3/ث)', 4),
            ('الوارد (م3/ث)', 5),
            ('المتوقع (م3/ث)', 6),
        ]
        for row in rows:
            dam_code = str(row[0])
            dam_id = dam_by_code.get(dam_code)
            if dam_id is None:
                skipped += 1
                continue
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'el-hydro-{date_s}-{dam_code}')
            base = [
                (attrs.get('السد'), str(dam_id), 'hydro_dam', dam_id),
                (attrs.get('تاريخ التقرير'), date_s, 'hydro_dam', dam_id),
            ]
            for label, idx in field_map:
                val = row[idx]
                base.append(
                    (
                        attrs.get(label),
                        '' if val is None else str(val),
                        'hydro_dam',
                        dam_id,
                    )
                )
            for attr, value, et, eid in base:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr,
                        sub_main=sub,
                        row_key=row_key,
                        value=value,
                        entity_type=et,
                        entity_id=eid,
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_inc_gen(self, sub, attrs, report_id, date_s, apply):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT id, event_time, description_ar, description_en
                FROM electricity_generationincident WHERE report_id = %s
                """,
                [report_id],
            )
            rows = cursor.fetchall()
        for inc_id, event_time, desc_ar, desc_en in rows:
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'el-incg-{date_s}-{inc_id}')
            pairs = [
                (attrs.get('تاريخ التقرير'), date_s),
                (attrs.get('وقت الحدث'), str(event_time or '')),
                (attrs.get('الوصف (عربي)'), str(desc_ar or '')),
                (attrs.get('الوصف (إنجليزي)'), str(desc_en or '')),
            ]
            for attr, value in pairs:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr, sub_main=sub, row_key=row_key, value=value
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_inc_grid(self, sub, attrs, report_id, date_s, apply):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT id, line_name, voltage_kv, action_ar, action_en
                FROM electricity_gridlineincident WHERE report_id = %s
                """,
                [report_id],
            )
            rows = cursor.fetchall()
        for inc_id, line_name, voltage, action_ar, action_en in rows:
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'el-incl-{date_s}-{inc_id}')
            pairs = [
                (attrs.get('تاريخ التقرير'), date_s),
                (attrs.get('اسم الخط'), str(line_name or '')),
                (attrs.get('الجهد (ك.ف)'), '' if voltage is None else str(voltage)),
                (attrs.get('الإجراء (عربي)'), str(action_ar or '')),
                (attrs.get('الإجراء (إنجليزي)'), str(action_en or '')),
            ]
            for attr, value in pairs:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr, sub_main=sub, row_key=row_key, value=value
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_notes(self, sub, attrs, report, date_s, apply):
        created = skipped = 0
        row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'el-notes-{date_s}')
        peak = report.get('peak_generation_time')
        ref = report.get('reference_hour')
        pairs = [
            (attrs.get('تاريخ التقرير'), date_s),
            (attrs.get('مجموعات الصيانة'), str(report.get('maintenance_groups_ar') or '')),
            (attrs.get('ملاحظات (عربي)'), str(report.get('notes_ar') or '')),
            (attrs.get('ملاحظات (إنجليزي)'), str(report.get('notes_en') or '')),
            (
                attrs.get('وقت ذروة التوليد'),
                peak.strftime('%H:%M') if peak else '',
            ),
            (attrs.get('ساعة مرجعية'), ref.strftime('%H:%M') if ref else ''),
        ]
        for attr, value in pairs:
            if attr is None or value == '':
                continue
            if apply:
                if _create_info(
                    attribute=attr, sub_main=sub, row_key=row_key, value=value
                ):
                    created += 1
                else:
                    skipped += 1
            else:
                created += 1
        return created, skipped
