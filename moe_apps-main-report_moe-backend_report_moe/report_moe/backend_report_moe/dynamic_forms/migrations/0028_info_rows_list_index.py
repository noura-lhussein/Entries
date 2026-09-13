# Generated manually for info-rows list hot path.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0027_info_report_date_unique"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="info",
            index=models.Index(
                fields=["attribute", "confirmed", "row_key", "-created_at"],
                name="dyn_info_rows_list_idx",
                condition=models.Q(archived=False, row_key__isnull=False),
            ),
        ),
    ]
