from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"categories", views.ProjectCategoryViewSet,
                basename="budget-category")
router.register(r"foundations", views.FoundationViewSet,
                basename="budget-foundation")
router.register(
    r"responsibles", views.ResponsibleViewSet, basename="budget-responsible"
)
router.register(r"project-types", views.ProjectTypeViewSet,
                basename="budget-project-type")
router.register(r"currencies", views.CurrencyViewSet,
                basename="budget-currency")
router.register(r"projects", views.ProjectViewSet, basename="budget-project")
router.register(
    r"project-change-logs",
    views.ProjectChangeLogViewSet,
    basename="budget-project-change-log",
)
router.register(r"milestones", views.MilestoneViewSet,
                basename="budget-milestone")
router.register(r"targets", views.TargetViewSet, basename="budget-target")
router.register(r"policies", views.PolicyViewSet, basename="budget-policy")
router.register(
    r"measure-units", views.MeasureUnitViewSet, basename="budget-measure-unit"
)
router.register(
    r"annual-budgets", views.AnnualBudgetViewSet, basename="budget-annual-budget"
)
router.register(
    r"project-transactions",
    views.ProjectTransactionViewSet,
    basename="budget-project-transaction",
)
router.register(
    r"milestone-transactions",
    views.MilestoneTransactionViewSet,
    basename="budget-milestone-transaction",
)
router.register(
    r"transactions", views.TransactionViewSet, basename="budget-transaction"
)
router.register(r"users", views.BudgetUserViewSet, basename="budget-user")

urlpatterns = [
    path("", include(router.urls)),
]
