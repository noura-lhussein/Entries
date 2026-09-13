"""Populate is_report_date on the date field of every daily-report title.

Which titles are daily reports cannot be derived from the field name: the two
incident logs below also label their date تاريخ التقرير, yet a dozen incidents on
one day is correct data. The exclusions are therefore listed by title, and every
other date-bearing title gets its date field marked.
"""

from django.db import migrations

# Not daily reports: event logs (many rows per day), target period bounds and
# alert start dates (many concurrent), and meetings (several a day).
NON_REPORT_TITLES = frozenset({
    'تسجيل حوادث التوليد',
    'تسجيل حوادث الخطوط',
})
# Prefixes rather than full names: the meeting title ends in a project phrase that
# is likely to be reworded, and matching it exactly once silently let it through.
NON_REPORT_TITLE_PREFIXES = ('أهداف تشغيلية', 'تنبيهات تشغيلية', 'اجتماعات')

# Titles carrying more than one date field, with the one that identifies the report.
PREFERRED_DATE_LABEL = {
    'تحديث محطات مياه الشرب': 'تاريخ التقييم',
}


def _is_report_title(name: str) -> bool:
    if name in NON_REPORT_TITLES:
        return False
    return not name.startswith(NON_REPORT_TITLE_PREFIXES)


def set_flags(apps, schema_editor):
    Attribute = apps.get_model('dynamic_forms', 'Attribute')
    Info = apps.get_model('dynamic_forms', 'Info')

    marked = []
    for attr in Attribute.objects.filter(type='date').select_related('title'):
        title = attr.title
        if title is None or not _is_report_title(title.name):
            continue
        preferred = PREFERRED_DATE_LABEL.get(title.name)
        if preferred and (attr.label or '').strip() != preferred:
            continue
        marked.append(attr.id)

    Attribute.objects.filter(id__in=marked).update(is_report_date=True)
    Info.objects.filter(attribute_id__in=marked).update(is_report_date=True)


def clear_flags(apps, schema_editor):
    apps.get_model('dynamic_forms', 'Attribute').objects.update(is_report_date=False)
    apps.get_model('dynamic_forms', 'Info').objects.update(is_report_date=False)


class Migration(migrations.Migration):

    dependencies = [('dynamic_forms', '0025_report_date_flag')]

    operations = [migrations.RunPython(set_flags, clear_flags)]
