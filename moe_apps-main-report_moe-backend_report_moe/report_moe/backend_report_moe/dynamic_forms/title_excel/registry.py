"""Excel import/export entry point.

``electricity.national`` and ``oil_gas.national`` use official multi-sheet
workbook handlers. All other titles use the attribute-driven dynamic handler.
Columns for Form Builder always resolve from Attribute rows where applicable.
"""

from .dynamic import DynamicTitleExcelHandler
from .electricity_daily import ElectricityDailyExcelHandler
from .oil_gas_daily import OilGasDailyExcelHandler

_default = DynamicTitleExcelHandler()
_electricity = ElectricityDailyExcelHandler()
_oil_gas = OilGasDailyExcelHandler()

_BY_CODE = {
    "electricity.national": _electricity,
    "oil_gas.national": _oil_gas,
}


def get_handler_for_title(title_or_name):
    code = getattr(title_or_name, "code", "") or ""
    if code in _BY_CODE:
        return _BY_CODE[code]
    return _default


def supports_title(_title_or_name) -> bool:
    return True
