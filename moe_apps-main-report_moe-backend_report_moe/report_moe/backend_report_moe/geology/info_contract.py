"""Schema contract for `geology/info_dashboard.py` — see water/info_contract.py."""

from __future__ import annotations

from .info_dashboard import TITLE_NATIONAL, TITLE_ORE_PRODUCTION

GEOLOGY_CONTRACT: dict[str, set[str]] = {
    TITLE_NATIONAL: {
        'geology_catalog_records',
        'geology_category_volcanic',
        'geology_category_sedimentary',
        'geology_category_modern',
    },
    # Not date-scoped — rows are keyed by `plan_year` (a number field), not a
    # type='date' attribute.
    TITLE_ORE_PRODUCTION: (
        {
            'product',
            'plan_year',
            'annual_plan_tons',
            'h1_plan_tons',
            'h1_executed_tons',
            'contract_count',
            'reserve_text',
        },
        False,
    ),
}
