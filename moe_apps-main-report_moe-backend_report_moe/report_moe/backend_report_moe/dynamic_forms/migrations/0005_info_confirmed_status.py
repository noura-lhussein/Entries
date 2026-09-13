from django.db import migrations, models


def forwards_bool_to_status(apps, schema_editor):
    Info = apps.get_model("dynamic_forms", "Info")
    for info in Info.objects.all():
        old = info.confirmed
        if isinstance(old, bool):
            info.confirmed_status = "accept" if old else "waiting"
            info.save(update_fields=["confirmed_status"])


def backwards_status_to_bool(apps, schema_editor):
    Info = apps.get_model("dynamic_forms", "Info")
    for info in Info.objects.all():
        status = getattr(info, "confirmed", "waiting")
        if isinstance(status, str):
            info.confirmed_status = status == "accept"
            info.save(update_fields=["confirmed_status"])


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0004_info_export_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="info",
            name="confirmed_status",
            field=models.CharField(
                choices=[
                    ("waiting", "Waiting"),
                    ("accept", "Accept"),
                    ("reject", "Reject"),
                ],
                default="waiting",
                max_length=10,
            ),
        ),
        migrations.RunPython(forwards_bool_to_status,
                             backwards_status_to_bool),
        migrations.RemoveField(
            model_name="info",
            name="confirmed",
        ),
        migrations.RenameField(
            model_name="info",
            old_name="confirmed_status",
            new_name="confirmed",
        ),
    ]
