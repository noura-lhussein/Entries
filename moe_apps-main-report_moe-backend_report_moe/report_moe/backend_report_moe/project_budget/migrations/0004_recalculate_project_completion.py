from decimal import Decimal

from django.db import migrations


def recalculate_project_completion(apps, schema_editor):
    Project = apps.get_model("project_budget", "Project")
    Milestone = apps.get_model("project_budget", "Milestone")

    status_weights = {
        "draft": Decimal("0"),
        "active": Decimal("50"),
        "on_hold": Decimal("25"),
        "completed": Decimal("100"),
    }

    for project in Project.objects.all().order_by("id"):
        milestones = list(
            Milestone.objects.filter(project_id=project.id, deleted=False)
            .exclude(status="cancelled")
            .only("status")
        )
        if not milestones:
            percentage = Decimal("0")
        else:
            total = sum(status_weights.get(m.status, Decimal("0"))
                        for m in milestones)
            percentage = (total / len(milestones)).quantize(Decimal("0.01"))
        Project.objects.filter(pk=project.id).update(
            percentage_completion=percentage)


class Migration(migrations.Migration):

    dependencies = [
        ("project_budget", "0003_regenerate_budget_codes_format"),
    ]

    operations = [
        migrations.RunPython(recalculate_project_completion,
                             migrations.RunPython.noop),
    ]
