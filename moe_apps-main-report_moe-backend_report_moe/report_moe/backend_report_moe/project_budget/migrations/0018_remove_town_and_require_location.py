import django.db.models.deletion
from django.db import migrations, models


def fill_missing_project_locations(apps, schema_editor):
    Project = apps.get_model("project_budget", "Project")
    Community = apps.get_model("locations", "Community")
    default_community = Community.objects.order_by("id").first()
    if default_community is None:
        return
    subdistrict = default_community.subdistrict
    district = subdistrict.district
    governorate = district.governorate
    Project.objects.filter(community_id__isnull=True).update(
        community_id=default_community.id,
        subdistrict_id=subdistrict.id,
        district_id=district.id,
        governorate_id=governorate.id,
    )


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("locations", "0001_initial"),
        ("project_budget", "0017_migrate_town_to_community"),
    ]

    operations = [
        migrations.RunPython(
            fill_missing_project_locations,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="project",
            name="town",
        ),
        migrations.AlterField(
            model_name="project",
            name="community",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="budget_projects",
                to="locations.community",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="district",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="budget_projects",
                to="locations.district",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="governorate",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="budget_projects",
                to="locations.governorate",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="subdistrict",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="budget_projects",
                to="locations.subdistrict",
            ),
        ),
        migrations.DeleteModel(
            name="Town",
        ),
    ]
