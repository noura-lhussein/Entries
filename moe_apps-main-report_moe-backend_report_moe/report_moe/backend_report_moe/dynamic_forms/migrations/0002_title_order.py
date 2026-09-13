from django.db import migrations, models


def assign_title_order(apps, schema_editor):
    Title = apps.get_model("dynamic_forms", "Title")
    for index, title in enumerate(Title.objects.all().order_by("id"), start=1):
        title.order = index
        title.save(update_fields=["order"])


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="title",
            name="order",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(assign_title_order, migrations.RunPython.noop),
    ]
