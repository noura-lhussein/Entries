"""Schema contract for `electricity/info_dashboard.py` — see water/info_contract.py."""

from __future__ import annotations

from .info_dashboard import (
    TITLE_FUEL,
    TITLE_GOV,
    TITLE_HYDRO,
    TITLE_INC_GEN,
    TITLE_INC_GRID,
    TITLE_NATIONAL,
    TITLE_NOTES,
    TITLE_PLANT,
    TITLE_UNITS,
)

ELECTRICITY_CONTRACT: dict[str, set[str]] = {
    TITLE_NATIONAL: {
        'nominal_capacity_mwh', 'total_generation_mwh_24h', 'gas_generation_mwh_24h',
        'steam_generation_mwh', 'steam_fuel_demand_tpd', 'gas_demand_mm3d',
        'total_fuel_demand_tpd', 'gas_consumed_mm3d', 'fuel_oil_consumed_tpd',
        'hydro_dams_capacity_mw', 'solar_capacity_mw', 'wind_capacity_mw',
        'fuel_oil_received_tpd', 'fuel_flow_consumed_tpd', 'fuel_oil_balance_tpd',
        'fuel_tank_max_capacity_tons', 'fuel_reserve_tons', 'fuel_tank_stock_tons',
        'fuel_reserve_pct', 'grid_frequency_hz', 'available_generated_power',
        'self_use_losses_mw', 'net_generation_mwh', 'industrial_self_use_mw',
        'generation_without_industrial_mw', 'hydro_output_mw', 'rotary_reserve_mw',
        'gov_consumed_mw', 'gov_allocated_mw', 'gov_excess_mw', 'gas_groups_mw',
        'steam_groups_mw', 'gas_import_mm3d', 'peak_generation_mw',
        'available_fuel_quantity', 'generation_incidents_count', 'grid_incidents_count',
    },
    # Rows are merged with TITLE_UNITS into one list in moeds — keys must match
    # TITLE_UNITS's exactly for that merge to work.
    TITLE_PLANT: {'generation_mwh', 'available_mw', 'unit_code', 'status', 'nominal_mw'},
    TITLE_UNITS: {'unit_code', 'nominal_mw', 'available_mw', 'generation_mwh', 'status'},
    TITLE_FUEL: {'current_stock_tons'},
    TITLE_GOV: {'consumed_mw', 'allocated_mw'},
    TITLE_HYDRO: {
        'front_level_m', 'back_level_m', 'generation_mwh',
        'outflow_m3s', 'inflow_m3s', 'expected_m3s',
    },
    TITLE_INC_GEN: {'event_time', 'description_ar', 'description_en'},
    TITLE_INC_GRID: {'line_name', 'voltage_kv', 'action_ar', 'action_en'},
    TITLE_NOTES: {
        'maintenance_groups', 'notes_ar', 'notes_en',
        'peak_generation_time', 'reference_hour',
    },
}
