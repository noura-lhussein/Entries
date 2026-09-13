from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "dynamic_forms",
            "0007_info_export_indexes_missing",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="info",
            name="row_key",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddIndex(
            model_name="info",
            index=models.Index(
                fields=["row_key", "sub_main"],
                name="dynamic_for_row_key_sub_idx",
            ),
        ),
    ]
