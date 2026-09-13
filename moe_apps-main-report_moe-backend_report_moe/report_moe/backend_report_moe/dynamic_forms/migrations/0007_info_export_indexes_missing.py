"""Create export indexes that 0004 recorded but were missing in some databases."""

from django.db import migrations


def create_missing_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS dynamic_for_confirm_8a1f2d_idx
            ON dynamic_forms_info (confirmed, sub_main_id)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS dynamic_for_user_id_4c9e21_idx
            ON dynamic_forms_info (user_id, confirmed)
            """
        )


def drop_optional_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS dynamic_for_confirm_8a1f2d_idx")
        cursor.execute("DROP INDEX IF EXISTS dynamic_for_user_id_4c9e21_idx")


class Migration(migrations.Migration):

    dependencies = [
        (
            "dynamic_forms",
            "0006_rename_dynamic_for_confirm_8a1f2d_idx_dynamic_for_confirm_8f4787_idx_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(create_missing_indexes, drop_optional_indexes),
    ]
