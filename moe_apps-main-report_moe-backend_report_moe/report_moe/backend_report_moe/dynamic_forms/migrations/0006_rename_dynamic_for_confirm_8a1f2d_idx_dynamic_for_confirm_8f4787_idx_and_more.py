# Safe follow-up to 0005: add textarea to Attribute.type choices only.
# Index renames from auto-generated makemigrations are skipped because
# 0004 indexes were never applied on this database (names do not exist).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0005_info_confirmed_status"),
    ]

    operations = [
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
                    ("city", "City"),
                    ("district", "District"),
                    ("image", "Image upload"),
                    ("file", "File upload"),
                ],
                max_length=50,
            ),
        ),
    ]
