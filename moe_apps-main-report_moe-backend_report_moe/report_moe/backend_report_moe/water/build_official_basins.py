"""Build Syria official hydro-basin GeoJSON from the MOE basins shapefile.

Run after updating source data:
    python manage.py sync_rainfall_basins
"""
from __future__ import annotations

from water.basin_catalog import DEFAULT_BASINS_SHAPEFILE
from water.basin_map_sync import sync_rainfall_basins_from_shapefile


def main() -> None:
    result = sync_rainfall_basins_from_shapefile(DEFAULT_BASINS_SHAPEFILE)
    print(f'Updated {result["basins_updated"]} basins and wrote {result["geojson_path"]}')


if __name__ == '__main__':
    main()
