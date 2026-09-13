# Generated manually for nested SubMainSection + Info entity link fields.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0016_user_can_manage_reference_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="submainsection",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="children",
                to="dynamic_forms.submainsection",
            ),
        ),
        migrations.AddField(
            model_name="info",
            name="entity_type",
            field=models.CharField(
                blank=True, db_index=True, default="", max_length=64
            ),
        ),
        migrations.AddField(
            model_name="info",
            name="entity_id",
            field=models.PositiveBigIntegerField(
                blank=True, db_index=True, null=True
            ),
        ),
        migrations.AddIndex(
            model_name="info",
            index=models.Index(
                fields=[
                    "entity_type",
                    "entity_id",
                    "confirmed",
                    "created_at",
                ],
                name="dynamic_for_entity_lookup_idx",
            ),
        ),
    ]
