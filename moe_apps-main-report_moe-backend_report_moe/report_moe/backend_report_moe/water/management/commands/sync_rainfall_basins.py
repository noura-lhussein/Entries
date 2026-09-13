from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from water.basin_catalog import DEFAULT_BASINS_SHAPEFILE
from water.basin_map_sync import sync_rainfall_basins_from_shapefile


class Command(BaseCommand):
    help = 'Sync water_rainfallbasin records and choropleth GeoJSON from the official basins shapefile.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=str(DEFAULT_BASINS_SHAPEFILE),
            help='Path to basins.shp (default: temp/basins_map/basins.shp).',
        )

    def handle(self, *args, **options):
        shp_path = Path(options['path'])
        try:
            result = sync_rainfall_basins_from_shapefile(shp_path)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {result["basins_updated"]} basins and wrote {result["geojson_path"]}',
            ),
        )
