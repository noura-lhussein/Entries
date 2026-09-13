from django.db import migrations

from project_budget.codes import budget_code, project_code


def regenerate_codes(apps, schema_editor):
    AnnualBudget = apps.get_model("project_budget", "AnnualBudget")
    Project = apps.get_model("project_budget", "Project")

    years = (
        AnnualBudget.objects.values_list("year", flat=True)
        .distinct()
        .order_by("year")
    )
    for year in years:
        letter_index = 0
        for budget in AnnualBudget.objects.filter(year=year).order_by("id"):
            budget.code = budget_code(year, letter_index)
            budget.save(update_fields=["code"])
            letter_index += 1

    for budget in AnnualBudget.objects.all().order_by("id"):
        project_index = 0
        for project in Project.objects.filter(annual_budget_id=budget.id).order_by("id"):
            project.code = project_code(budget.code, project_index)
            project.save(update_fields=["code"])
            project_index += 1


class Migration(migrations.Migration):

    dependencies = [
        ("project_budget", "0002_annualbudget_code"),
    ]

    operations = [
        migrations.RunPython(regenerate_codes, migrations.RunPython.noop),
    ]
