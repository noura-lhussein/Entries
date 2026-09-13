"""Re-exports of report_moe models under the names the portal read-paths use.

Before the merge moeds could not import report_moe's models, so it declared partial
read-only mirrors over the same tables and reached them through a second connection.
One backend removes both the mirrors and the connection: these are aliases now, and
the objects behind them are the real, complete models.

The `Report*` prefix is kept deliberately — it marks, at every call site, that the
data is authored in the reporting side of the system and only displayed here.
"""

from dynamic_forms.models import (
    Attribute as ReportDynamicFormsAttribute,
)
from dynamic_forms.models import (
    Info as ReportDynamicFormsInfo,
)
from dynamic_forms.models import (
    Title as ReportDynamicFormsTitle,
)
from dynamic_forms.models import (
    TitleCategory as ReportDynamicFormsTitleCategory,
)
from locations.models import Governorate as ReportGovernorate
from project_budget.models import (
    Foundation as ReportFoundation,
)
from project_budget.models import (
    Project as ReportBudgetProject,
)

__all__ = [
    "ReportBudgetProject",
    "ReportDynamicFormsAttribute",
    "ReportDynamicFormsInfo",
    "ReportDynamicFormsTitle",
    "ReportDynamicFormsTitleCategory",
    "ReportFoundation",
    "ReportGovernorate",
]
