from __future__ import annotations

from django.db import migrations


def refresh_resource_formats(apps, schema_editor):
    from datasets.services import backfill_resource_formats

    backfill_resource_formats()


class Migration(migrations.Migration):
    dependencies = [
        ('datasets', '0004_datasetresource'),
    ]

    operations = [
        migrations.RunPython(refresh_resource_formats, migrations.RunPython.noop),
    ]
