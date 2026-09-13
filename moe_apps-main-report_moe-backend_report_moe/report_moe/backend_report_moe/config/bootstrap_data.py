from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.core.management import call_command
from django.core.management.base import OutputWrapper
from electricity.gis_layer_catalog import DEFAULT_ELECTRICITY_GIS_DIR
from gis.geology_layer_catalog import DEFAULT_GEOLOGY_DIR
from gis.layer_catalog import DEFAULT_BOUNDARIES_DIR
from gis.water_layer_catalog import DEFAULT_WATER_DIR

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _electricity_gis_bootstrap_step() -> BootstrapStep:
    scan_dir = os.environ.get('MOE_ELECTRICITY_GIS_SCAN_DIR', '').strip()
    if scan_dir and Path(scan_dir).is_dir():
        return BootstrapStep(
            command='import_electricity_gis_layers',
            label='Electricity GIS layers (flat shapefile scan)',
            kwargs={'scan': True, 'path': scan_dir},
            optional=True,
        )
    return BootstrapStep(
        command='import_electricity_gis_layers',
        label='Electricity GIS layers',
        kwargs={},
        required_paths=(DEFAULT_ELECTRICITY_GIS_DIR,),
        optional=True,
    )


@dataclass(frozen=True, slots=True)
class BootstrapStep:
    command: str
    label: str
    kwargs: dict[str, Any]
    required_paths: tuple[Path, ...] = ()
    optional: bool = False


def _drinking_water_workbook() -> Path:
    return BACKEND_ROOT / 'water' / 'data' / 'drinking_water_stations.xlsx'


def bootstrap_steps(*, include_gis: bool = True, include_external_water: bool = False) -> list[BootstrapStep]:
    """Ordered bootstrap pipeline: auth → GIS → water → projects → oil & gas → electricity."""
    steps: list[BootstrapStep] = [
        BootstrapStep(
            command='seed_demo_user',
            label='Demo portal user',
            kwargs={},
        ),
    ]

    if include_gis:
        steps.extend([
            BootstrapStep(
                command='import_admin_boundaries',
                label='Administrative boundaries',
                kwargs={},
                required_paths=(DEFAULT_BOUNDARIES_DIR,),
                optional=True,
            ),
            BootstrapStep(
                command='import_water_layers',
                label='Water map layers',
                kwargs={},
                required_paths=(DEFAULT_WATER_DIR,),
                optional=True,
            ),
            BootstrapStep(
                command='import_geology_layers',
                label='Geology map layers',
                kwargs={},
                required_paths=(DEFAULT_GEOLOGY_DIR,),
                optional=True,
            ),
        ])

    # Water master data imports moved to report_moe — moeds is read-only on these tables.
    # See: report_moe/master_data/management/commands/import_drinking_stations_master.py

    if include_external_water:
        steps.extend([
            BootstrapStep(
                command='sync_rainfall_basins',
                label='Rainfall basins',
                kwargs={},
                optional=True,
            ),
            BootstrapStep(
                command='import_rainfall_data',
                label='Rainfall observations',
                kwargs={},
                optional=True,
            ),
            BootstrapStep(
                command='import_dam_data',
                label='Dam storage readings',
                kwargs={},
                optional=True,
            ),
            BootstrapStep(
                command='import_euphrates_cascade',
                label='Euphrates cascade readings',
                kwargs={},
                optional=True,
            ),
        ])

    # Oil & gas and electricity master data moved to report_moe.
    # See: report_moe/master_data/management/commands/
    #   - seed_minister_ops.py (catalogs)
    #   - seed_electricity_daily_catalogs.py
    #   - import_pos2_fuel_stations.py
    steps.append(_electricity_gis_bootstrap_step())
    return steps


def _missing_paths(paths: Sequence[Path]) -> list[Path]:
    return [path for path in paths if not path.exists()]


def run_bootstrap(
    stdout: OutputWrapper,
    *,
    include_gis: bool = True,
    include_external_water: bool = False,
    only: Iterable[str] | None = None,
    skip_missing: bool = True,
) -> dict[str, int]:
    """Run the unified bootstrap pipeline and return run/skip/error counts."""
    selected = {part.strip().lower() for part in only} if only else None
    steps = bootstrap_steps(include_gis=include_gis, include_external_water=include_external_water)
    counts = {'ran': 0, 'skipped': 0, 'errors': 0}

    for step in steps:
        if selected and not _step_matches(step, selected):
            continue

        missing = _missing_paths(step.required_paths)
        if missing and skip_missing:
            stdout.write(
                f"Skipping {step.label}: missing {[str(path) for path in missing]}"
            )
            counts['skipped'] += 1
            continue
        if missing and not step.optional:
            raise FileNotFoundError(
                f"Required data missing for {step.label}: {', '.join(str(path) for path in missing)}"
            )

        stdout.write(f"Running {step.label} ({step.command})...")
        try:
            call_command(step.command, stdout=stdout, stderr=stdout, **step.kwargs)
            counts['ran'] += 1
        except Exception as exc:  # noqa: BLE001 - surface bootstrap failures clearly
            counts['errors'] += 1
            if step.optional:
                stdout.write(f"Skipped {step.label} after error: {exc}")
                counts['skipped'] += 1
                continue
            raise

    return counts


def _step_matches(step: BootstrapStep, selected: set[str]) -> bool:
    tokens = {
        step.command.lower(),
        step.label.lower(),
        step.command.replace('_', '-').lower(),
    }
    if step.command == 'seed_demo_user' and {'auth', 'user', 'users'} & selected:
        return True
    if step.command.startswith('import_admin') and {'gis', 'admin', 'boundaries'} & selected:
        return True
    if step.command.startswith('import_water_layers') and {'gis', 'water-layers'} & selected:
        return True
    if step.command.startswith('import_geology') and {'gis', 'geology'} & selected:
        return True
    if 'water' in selected and any(
        token in step.command for token in ('drinking_water', 'rainfall', 'dam', 'euphrates', 'classify')
    ):
        return True
    if 'projects' in selected and 'development' in step.command:
        return True
    if {'oil', 'oil-gas', 'oil_gas'} & selected and step.command in {
        'seed_minister_ops', 'import_pos2_fuel_stations',
    }:
        return True
    if {'electricity', 'power'} & selected and step.command in {
        'seed_electricity_ops', 'import_electricity_gis_layers',
    }:
        return True
    return bool(tokens & selected)
