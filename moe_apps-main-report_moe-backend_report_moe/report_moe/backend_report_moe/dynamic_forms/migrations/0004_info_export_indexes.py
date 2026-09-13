from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0003_user_can_export_reports"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="info",
            index=models.Index(
                fields=["confirmed", "sub_main"],
                name="dynamic_for_confirm_8a1f2d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="info",
            index=models.Index(
                fields=["user", "confirmed"],
                name="dynamic_for_user_id_4c9e21_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="info",
            index=models.Index(
                fields=["created_at"],
                name="dynamic_for_created_2b7f90_idx",
            ),
        ),
    ]
