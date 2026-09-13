"""Shared constants for dynamic title Excel import/export."""

COL_MAIN_SECTION = "القسم الرئيسي"
COL_SUB_MAIN = "القسم الفرعي"
COL_REGION = "المنطقة أو المحافظة"
COL_GOVERNORATE = "المحافظة"
COL_LOCATION = "الموقع"

SECTION_COLUMN_LABELS = (
    COL_MAIN_SECTION,
    COL_SUB_MAIN,
    COL_REGION,
)

REGION_HEADER_ALIASES = frozenset(
    {COL_REGION, COL_GOVERNORATE, COL_LOCATION}
)

# Attribute types that cannot be filled via Excel
NON_EXCEL_ATTRIBUTE_TYPES = frozenset({"image", "file"})
