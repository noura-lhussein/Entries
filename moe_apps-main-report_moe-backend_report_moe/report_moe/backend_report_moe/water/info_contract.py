"""
Declares exactly which report_moe Title codes / Attribute keys `water/info_dashboard.py`
depends on, so `manage.py check_info_contract` can verify they still exist before a
seed-command edit or an admin renaming a field silently breaks a dashboard.

Keep this in sync by hand when info_dashboard.py starts/stops reading a key — it is
the single list a reviewer checks against a diff, and the one thing the contract
command actually runs against the live report_moe database.
"""

from __future__ import annotations

from .info_dashboard import TITLE_DAM_ENTITY, TITLE_EUPHRATES, TITLE_NATIONAL, TITLE_RAINFALL_ENTITY

# title_code -> {attribute keys read by name; a title always needs exactly one
# type='date' attribute too, checked separately}
WATER_CONTRACT: dict[str, set[str]] = {
    TITLE_NATIONAL: {
        'rainfall_stations_reporting',
        'rainfall_total_mm',
        'dams_with_readings',
        'dam_storage_avg_mcm',
        'dam_storage_total_mcm',
        'drinking_stations_total',
        'drinking_stations_operational',
    },
    TITLE_RAINFALL_ENTITY: {
        'precipitation_mm',
    },
    TITLE_DAM_ENTITY: {
        'storage_mcm',
    },
    TITLE_EUPHRATES: {
        'report_label',
        'inflow_jarabulus',
        'tishreen_level_m',
        'tishreen_storage_mcm',
        'tishreen_outflow',
        'tishreen_generation_mwh',
        'furat_level_m',
        'furat_storage_mcm',
        'furat_outflow',
        'furat_generation_mwh',
        'kadiran_outflow',
        'kadiran_generation_mwh',
        'al_jalab_discharge',
        'total_generation_mwh',
    },
}
