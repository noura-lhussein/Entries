"""Drop the unmanaged mirror models over report_moe tables.

They existed so this project could read report_moe's tables through a second
connection. With one backend those tables are reachable by plain ORM, and
`display_models` now re-exports the real models under the same names — so the
mirror model *state* has to go too, or Django keeps seeing models the code no
longer defines.

`managed = False` throughout: these operations change migration state only and
issue no DDL. The tables belong to report_moe's own migrations.
"""

from django.db import migrations

MIRROR_MODELS = [
    'ReportBudgetProject',
    'ReportDynamicFormsAttribute',
    'ReportDynamicFormsInfo',
    'ReportDynamicFormsTitle',
    'ReportDynamicFormsTitleCategory',
    'ReportFoundation',
    'ReportGovernorate',
]


class Migration(migrations.Migration):

    dependencies = [('projects', '0010_reportbudgetproject_reportdynamicformsattribute_and_more')]

    operations = [migrations.DeleteModel(name=name) for name in MIRROR_MODELS]
