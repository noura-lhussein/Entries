# Generated manually for Info search/read indexes.

from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False  # allow CREATE INDEX CONCURRENTLY on Postgres

    dependencies = [
        ('dynamic_forms', '0020_entry_form_metadata'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddIndex(
                    model_name='info',
                    index=models.Index(
                        fields=['confirmed', 'attribute', '-created_at'],
                        name='dyn_info_conf_attr_created_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='info',
                    index=models.Index(
                        fields=['sub_main', 'confirmed', '-created_at'],
                        name='dyn_info_sub_conf_created_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='info',
                    index=models.Index(
                        fields=['attribute', 'sub_main', 'confirmed'],
                        name='dyn_info_attr_sub_conf_idx',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        """
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS dyn_info_conf_attr_created_idx
                        ON dynamic_forms_info (confirmed, attribute_id, created_at DESC);
                        """,
                        """
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS dyn_info_sub_conf_created_idx
                        ON dynamic_forms_info (sub_main_id, confirmed, created_at DESC);
                        """,
                        """
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS dyn_info_attr_sub_conf_idx
                        ON dynamic_forms_info (attribute_id, sub_main_id, confirmed);
                        """,
                    ],
                    reverse_sql=[
                        'DROP INDEX CONCURRENTLY IF EXISTS dyn_info_conf_attr_created_idx;',
                        'DROP INDEX CONCURRENTLY IF EXISTS dyn_info_sub_conf_created_idx;',
                        'DROP INDEX CONCURRENTLY IF EXISTS dyn_info_attr_sub_conf_idx;',
                    ],
                ),
            ],
        ),
    ]
