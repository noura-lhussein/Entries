from django.contrib import admin

from .models import (
    AnnualBudget,
    BudgetUserScope,
    Currency,
    Foundation,
    MeasureUnit,
    Milestone,
    MilestoneTransaction,
    Policy,
    Project,
    ProjectCategory,
    ProjectTransaction,
    ProjectType,
    Responsible,
    Target,
    Transaction,
)

admin.site.register(ProjectCategory)
admin.site.register(Foundation)
admin.site.register(BudgetUserScope)
admin.site.register(Responsible)
admin.site.register(ProjectType)
admin.site.register(Currency)
admin.site.register(Project)
admin.site.register(Milestone)
admin.site.register(AnnualBudget)
admin.site.register(ProjectTransaction)
admin.site.register(MilestoneTransaction)
admin.site.register(Transaction)
admin.site.register(Target)
admin.site.register(Policy)
admin.site.register(MeasureUnit)
