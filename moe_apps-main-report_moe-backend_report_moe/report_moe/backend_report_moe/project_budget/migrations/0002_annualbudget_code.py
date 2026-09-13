from django.db import migrations, models


def populate_budget_codes(apps, schema_editor):
    AnnualBudget = apps.get_model("project_budget", "AnnualBudget")
    Project = apps.get_model("project_budget", "Project")

    for budget in AnnualBudget.objects.all().order_by("id"):
        if not budget.code:
            budget.code = f"{budget.year}-{int(budget.project_type_id):03d}"
            budget.save(update_fields=["code"])

    for budget in AnnualBudget.objects.all().order_by("id"):
        prefix = f"{budget.code}-"
        seq = 0
        for project in Project.objects.filter(annual_budget_id=budget.id).order_by("id"):
            if project.code:
                suffix = project.code[len(prefix):] if project.code.startswith(
                    prefix) else ""
                try:
                    seq = max(seq, int(suffix))
                except ValueError:
                    pass
                continue
            seq += 1
            project.code = f"{budget.code}-{seq:03d}"
            project.save(update_fields=["code"])


class Migration(migrations.Migration):

    dependencies = [
        ("project_budget", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="annualbudget",
            name="code",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.RunPython(populate_budget_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="annualbudget",
            name="code",
            field=models.CharField(
                blank=True, default="", max_length=20, unique=True),
        ),
    ]
