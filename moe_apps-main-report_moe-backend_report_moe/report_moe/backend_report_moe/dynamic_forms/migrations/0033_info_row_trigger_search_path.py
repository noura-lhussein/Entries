"""Pin Info-row trigger functions to schema report_moe.

The statement triggers on dynamic_forms_info call dyn_info_row_refresh()
without a schema qualifier. SQL clients (DBeaver, psql) often use
search_path "$user", public — so UPDATE fails with:

    function dyn_info_row_refresh(uuid[]) does not exist

Django's connection uses search_path report_moe,moeds,public, which is why
the app itself was fine. SET search_path on the functions makes them resolve
regardless of the session.
"""

from django.db import migrations

SQL = """
ALTER FUNCTION report_moe.dyn_safe_date(text)
    SET search_path TO report_moe, public;
ALTER FUNCTION report_moe.dyn_info_row_refresh(uuid[])
    SET search_path TO report_moe, public;
ALTER FUNCTION report_moe.dyn_info_row_tg_ins()
    SET search_path TO report_moe, public;
ALTER FUNCTION report_moe.dyn_info_row_tg_upd()
    SET search_path TO report_moe, public;
ALTER FUNCTION report_moe.dyn_info_row_tg_del()
    SET search_path TO report_moe, public;
ALTER FUNCTION report_moe.dyn_info_row_tg_trunc()
    SET search_path TO report_moe, public;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0032_info_row_triggers"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL, reverse_sql=migrations.RunSQL.noop),
    ]
