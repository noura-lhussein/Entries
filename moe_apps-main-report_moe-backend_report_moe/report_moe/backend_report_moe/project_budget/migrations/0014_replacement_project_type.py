from django.db import migrations

REPLACEMENT_NAME_AR = "مشاريع الاستبدال والتجديد"
REPLACEMENT_NAME_EN = "Replacement and Renewal Projects"
ONGOING_NAME_AR = "المشاريع المباشر بها"
ONGOING_NAME_EN = "Ongoing Projects"


def seed_project_types(apps, schema_editor):
    ProjectType = apps.get_model("project_budget", "ProjectType")

    ProjectType.objects.filter(name_ar="مباشر بها", deleted=False).update(
        name_ar=ONGOING_NAME_AR,
        name_en=ONGOING_NAME_EN,
    )

    exists = ProjectType.objects.filter(
        name_ar=REPLACEMENT_NAME_AR,
        deleted=False,
    ).exists()
    if not exists:
        ProjectType.objects.create(
            name_ar=REPLACEMENT_NAME_AR,
            name_en=REPLACEMENT_NAME_EN,
            deleted=False,
        )


def reverse_seed(apps, schema_editor):
    ProjectType = apps.get_model("project_budget", "ProjectType")

    ProjectType.objects.filter(
        name_ar=REPLACEMENT_NAME_AR,
        deleted=False,
    ).delete()

    ProjectType.objects.filter(name_ar=ONGOING_NAME_AR, deleted=False).update(
        name_ar="مباشر بها",
        name_en="started",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("project_budget", "0013_projectcategory_code"),
    ]

    operations = [
        migrations.RunPython(seed_project_types, reverse_seed),
    ]
