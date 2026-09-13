from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project_budget", "0006_rename_allocated_amount_project_approved_budget_and_more"),
    ]

    operations = [
        # allocated_amount was renamed to Approved_budget in 0006; that column holds
        # the original values and becomes proposed_budget (user intent).
        migrations.RemoveField(
            model_name="project",
            name="Proposed_budget",
        ),
        migrations.RenameField(
            model_name="project",
            old_name="Approved_budget",
            new_name="proposed_budget",
        ),
        migrations.RenameField(
            model_name="project",
            old_name="Budget_expenditure",
            new_name="budget_expenditure",
        ),
        migrations.AddField(
            model_name="project",
            name="approved_budget",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=14),
        ),
    ]
