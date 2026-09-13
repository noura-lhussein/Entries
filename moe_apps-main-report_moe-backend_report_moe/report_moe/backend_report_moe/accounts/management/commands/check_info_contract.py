"""
Assert every report_moe Title/Attribute a sector's info_dashboard.py depends on
still exists — same role as `check_write_permissions`, but for the schema
contract instead of DB grants.

Without this, a renamed/deleted field in report_moe's Form Builder breaks a
dashboard silently: no exception, no 500, just a KPI quietly going to `None`
or a whole section reporting "no data". Run this in CI/deploy so that surfaces
loudly instead.

Each sector that has migrated to code/key-based Info reads declares its
contract in `<sector>/info_contract.py` as a module-level `<SECTOR>_CONTRACT:
dict[str, set[str] | tuple[set[str], bool]]` mapping a Title.code to the
Attribute.keys read under it. A plain `set[str]` requires the title to carry a
`type='date'` attribute (the common case: dashboards scope reads by year);
pass `(keys, False)` for a title that isn't date-scoped (e.g. keyed by a
`plan_year` number field instead). This command discovers every such module
and checks it against the live reporting tables (schema `report_moe`,
alias).

Usage:
  python manage.py check_info_contract
Exit code 1 on any missing title/attribute.
"""

from __future__ import annotations

import importlib

from django.core.management.base import BaseCommand
from projects.display_models import ReportDynamicFormsAttribute, ReportDynamicFormsTitle

# Add a sector's module path here once it has an info_contract.py.
CONTRACT_MODULES = (
    'water.info_contract',
    'geology.info_contract',
    'oil_gas.info_contract',
    'electricity.info_contract',
)


def _load_contracts() -> dict[str, dict[str, set[str]]]:
    """module path -> {title_code: {attribute keys}}"""
    contracts: dict[str, dict[str, set[str]]] = {}
    for module_path in CONTRACT_MODULES:
        module = importlib.import_module(module_path)
        for name in dir(module):
            if name.endswith('_CONTRACT'):
                contracts[module_path] = getattr(module, name)
    return contracts


class Command(BaseCommand):
    help = "Verify report_moe Title/Attribute codes referenced by moeds sector dashboards still exist."

    def handle(self, *args, **options):
        errors: list[str] = []
        contracts = _load_contracts()

        if not contracts:
            self.stdout.write(self.style.WARNING('No info_contract modules found — nothing to check.'))
            return

        for module_path, contract in contracts.items():
            for title_code, spec in contract.items():
                if isinstance(spec, tuple):
                    required_keys, requires_date = spec
                else:
                    required_keys, requires_date = spec, True

                title = (
                    ReportDynamicFormsTitle.objects
                    .filter(code=title_code)
                    .first()
                )
                if title is None:
                    errors.append(
                        f'{module_path}: Title code "{title_code}" not found in report_moe.'
                    )
                    continue
                if title.deleted:
                    errors.append(
                        f'{module_path}: Title code "{title_code}" ({title.name}) is soft-deleted.'
                    )
                if not title.is_system:
                    errors.append(
                        f'{module_path}: Title code "{title_code}" ({title.name}) is not marked '
                        f'is_system — nothing stops it from being edited/deleted from the UI.'
                    )

                existing_keys = set(
                    ReportDynamicFormsAttribute.objects
                    .filter(title_id=title.id)
                    .exclude(key='')
                    .values_list('key', flat=True)
                )
                missing_keys = required_keys - existing_keys
                for key in sorted(missing_keys):
                    errors.append(
                        f'{module_path}: Attribute key "{key}" not found under Title '
                        f'"{title_code}" ({title.name}).'
                    )

                if requires_date:
                    has_date_attr = (
                        ReportDynamicFormsAttribute.objects
                        .filter(title_id=title.id, type='date')
                        .exists()
                    )
                    if not has_date_attr:
                        errors.append(
                            f'{module_path}: Title "{title_code}" ({title.name}) has no type=date '
                            f'attribute — date-scoped reads will silently return nothing.'
                        )

        for error in errors:
            self.stderr.write(self.style.ERROR(f'ERROR {error}'))

        if errors:
            self.stderr.write(self.style.ERROR(f'FAILED — {len(errors)} problem(s).'))
            raise SystemExit(1)

        checked_titles = sum(len(c) for c in contracts.values())
        self.stdout.write(
            self.style.SUCCESS(
                f'OK — {len(contracts)} sector contract(s), {checked_titles} title(s) verified.'
            )
        )
