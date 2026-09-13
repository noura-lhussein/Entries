import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0001_initial"),
        ("dynamic_forms", "0011_user_can_manage_budget"),
    ]

    operations = [
        migrations.AddField(
            model_name="submainsection",
            name="location_district",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="report_sub_sections",
                to="locations.district",
            ),
        ),
        migrations.AddField(
            model_name="info",
            name="loc_community",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="report_infos",
                to="locations.community",
            ),
        ),
        migrations.AddField(
            model_name="info",
            name="loc_district",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="report_infos",
                to="locations.district",
            ),
        ),
        migrations.AddField(
            model_name="info",
            name="loc_governorate",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="report_infos",
                to="locations.governorate",
            ),
        ),
        migrations.AddField(
            model_name="info",
            name="loc_subdistrict",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="report_infos",
                to="locations.subdistrict",
            ),
        ),
        migrations.AlterField(
            model_name="attribute",
            name="type",
            field=models.CharField(
                choices=[
                    ("text", "Text"),
                    ("textarea", "Text Area"),
                    ("number", "Number"),
                    ("date", "Date"),
                    ("boolean", "Boolean/Checkbox"),
                    ("select", "Dropdown"),
                    ("city", "City / Governorate"),
                    ("district", "District"),
                    ("sub_district", "Sub-district"),
                    ("community", "Community"),
                    ("image", "Image upload"),
                    ("file", "File upload"),
                ],
                max_length=50,
            ),
        ),
    ]
