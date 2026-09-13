"""Schema contract for `oil_gas/info_dashboard.py` — see water/info_contract.py."""

from __future__ import annotations

from .info_dashboard import TITLE_NATIONAL

OIL_GAS_CONTRACT: dict[str, set[str]] = {
    TITLE_NATIONAL: {
        'total_oil_production_bbl',
        'total_crude_transferred_bbl',
        'local_clean_gas_mm3',
        'clean_gas_import_azerbaijan_mm3',
        'clean_gas_import_jordan_mm3',
        'total_clean_gas_mm3',
        'clean_gas_distributed_mm3',
        'electricity_clean_gas_consumption_mm3',
        'mazut_sold_thu_fri_m3',
        'gasoline_90_95_sold_thu_fri_m3',
        'domestic_lpg_sold_m3',
        'fuel_oil_sold_m3',
        'brent_crude_price_usd_bbl',
        'gas_price_usd_mmbtu',
    },
}
