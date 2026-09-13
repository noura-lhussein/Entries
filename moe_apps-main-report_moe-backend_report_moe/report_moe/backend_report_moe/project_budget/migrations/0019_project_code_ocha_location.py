from django.db import migrations

from project_budget.codes import project_code


def regenerate_project_codes_with_ocha(apps, schema_editor):
    Project = apps.get_model("project_budget", "Project")
    projects = (
        Project.objects.select_related(
            "annual_budget",
            "community",
            "community__subdistrict",
        )
        .order_by("annual_budget_id", "community_id", "id")
    )
    counters: dict[tuple[str, str, str], int] = {}
    for project in projects:
        budget = project.annual_budget
        if not budget or not budget.code:
            continue
        community = project.community
        if not community or not community.subdistrict:
            continue
        subdistrict_code = (community.subdistrict.code or "").strip()
        community_code = (community.code or "").strip()
        if not subdistrict_code or not community_code:
            continue
        key = (budget.code, subdistrict_code, community_code)
        index = counters.get(key, 0)
        project.code = project_code(
            budget.code, subdistrict_code, community_code, index)
        project.save(update_fields=["code"])
        counters[key] = index + 1


class Migration(migrations.Migration):

    dependencies = [
        ("project_budget", "0018_remove_town_and_require_location"),
    ]

    operations = [
        migrations.RunPython(
            regenerate_project_codes_with_ocha,
            migrations.RunPython.noop,
        ),
    ]
