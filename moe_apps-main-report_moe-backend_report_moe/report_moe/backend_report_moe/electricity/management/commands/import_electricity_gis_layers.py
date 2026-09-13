from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from map_layers.shapefile_utils import iter_shapefile_features

from electricity.gis_layer_catalog import (
    DEFAULT_ELECTRICITY_GIS_DIR,
    ELECTRICITY_400KV_SEGMENT_FILES,
    ELECTRICITY_GIS_LAYER_BY_ID,
    ELECTRICITY_GIS_LAYER_SPECS,
    electricity_gis_feature_name,
    normalize_electricity_gis_properties,
)
from electricity.gis_services import (
    clear_electricity_gis_layer_features,
    insert_electricity_gis_feature,
    upsert_electricity_gis_layer_catalog,
)
from electricity.gis_shapefile_lines import (
    line_geometry_from_point_series_shapefile,
    segment_line_properties,
)
from electricity.gis_source_discovery import (
    GisImportSource,
    ImportMode,
    discover_gis_sources,
    layer_ids_from_sources,
    voltage_from_classification,
)


class Command(BaseCommand):
    help = (
        'Import electricity sector GIS shapefiles into PostGIS. '
        'Use --scan to classify a flat directory of shapefiles (e.g. Desktop export).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=str(DEFAULT_ELECTRICITY_GIS_DIR),
            help='GIS directory (structured data/gis or flat scanned folder).',
        )
        parser.add_argument(
            '--scan',
            action='store_true',
            help='Scan --path for loose shapefiles and classify by name/geometry.',
        )
        parser.add_argument(
            '--layer',
            type=str,
            default='',
            help='Import a single layer id (e.g. power-gis-lines-230).',
        )

    def handle(self, *args, **options):
        source_dir = Path(options['path'])
        if not source_dir.is_dir():
            raise CommandError(f'Electricity GIS directory not found: {source_dir}')

        upsert_electricity_gis_layer_catalog()

        if options['scan']:
            self._import_scanned(source_dir, options['layer'])
            return

        self._import_structured(source_dir, options['layer'])

    def _import_scanned(self, source_dir: Path, layer_filter: str) -> None:
        sources = discover_gis_sources(source_dir)
        if not sources:
            raise CommandError(f'No electricity GIS shapefiles found in {source_dir}')

        layer_ids = layer_ids_from_sources(sources)
        if layer_filter:
            if layer_filter not in layer_ids:
                raise CommandError(f'Layer {layer_filter!r} not found in scanned sources.')
            layer_ids = [layer_filter]

        sources_by_layer: dict[str, list[GisImportSource]] = {layer_id: [] for layer_id in layer_ids}
        split_sources: list[GisImportSource] = []
        for source in sources:
            if source.layer_id not in sources_by_layer:
                continue
            if source.mode == ImportMode.SPLIT_BY_VOLTAGE:
                split_sources.append(source)
                continue
            sources_by_layer[source.layer_id].append(source)

        # Split-voltage substation files feed multiple layers — clear every target layer once.
        split_targets = {
            'power-gis-substations-66',
            'power-gis-substations-230',
            'power-gis-substations-400',
        }
        if split_sources:
            layer_ids = list(dict.fromkeys([*layer_ids, *split_targets]))

        for layer_id in layer_ids:
            clear_electricity_gis_layer_features(layer_id)

        total = 0
        counts: dict[str, int] = {layer_id: 0 for layer_id in layer_ids}
        for layer_id in layer_ids_from_sources(sources):
            if layer_filter and layer_id != layer_filter:
                continue
            for source in sources_by_layer.get(layer_id, []):
                counts[layer_id] += self._import_source(layer_id, source)

        for source in split_sources:
            split_counts = self._import_split_voltage_substations(source.shp_path, accumulate=True)
            for layer_id, count in split_counts.items():
                counts[layer_id] = counts.get(layer_id, 0) + count

        for layer_id in layer_ids_from_sources(sources):
            if layer_filter and layer_id != layer_filter:
                continue
            total += counts.get(layer_id, 0)
            file_count = len(sources_by_layer.get(layer_id, []))
            if layer_id in split_targets and split_sources:
                file_count += 1 if layer_id in {'power-gis-substations-66', 'power-gis-substations-230', 'power-gis-substations-400'} else 0
            self.stdout.write(
                self.style.SUCCESS(f'{layer_id}: imported {counts.get(layer_id, 0)} features from {file_count} file(s)')
            )

        self.stdout.write(self.style.SUCCESS(f'Done. Imported {total} electricity GIS features total.'))

    def _import_structured(self, source_dir: Path, layer_filter: str) -> None:
        layers = ELECTRICITY_GIS_LAYER_SPECS
        if layer_filter:
            layers = [layer for layer in ELECTRICITY_GIS_LAYER_SPECS if layer.id == layer_filter]
            if not layers:
                raise CommandError(f'Unknown layer id: {layer_filter}')

        total = 0
        for layer in layers:
            file_path = source_dir / layer.file
            if not file_path.is_file():
                raise CommandError(f'Missing shapefile: {file_path}')

            clear_electricity_gis_layer_features(layer.id)
            imported = 0

            for _field_names, raw_props, geometry in iter_shapefile_features(file_path):
                properties = normalize_electricity_gis_properties(layer.id, raw_props)
                name = electricity_gis_feature_name(layer.id, properties)
                insert_electricity_gis_feature(layer.id, name, properties, geometry)
                imported += 1

            if layer.id == 'power-gis-lines-400':
                for rel in ELECTRICITY_400KV_SEGMENT_FILES:
                    segment_path = source_dir / rel
                    if not segment_path.is_file():
                        raise CommandError(f'Missing 400 kV segment shapefile: {segment_path}')
                    imported += self._import_point_series_line(layer.id, segment_path, voltage_kv=400)

            total += imported
            detail = layer.file
            if layer.id == 'power-gis-lines-400':
                detail = f'{layer.file} + {len(ELECTRICITY_400KV_SEGMENT_FILES)} segment files'
            self.stdout.write(
                self.style.SUCCESS(f'{layer.id}: imported {imported} features from {detail}')
            )

        self.stdout.write(self.style.SUCCESS(f'Done. Imported {total} electricity GIS features total.'))

    def _import_source(self, layer_id: str, source: GisImportSource) -> int:
        if source.mode == ImportMode.POINT_SERIES_LINE:
            return self._import_point_series_line(layer_id, source.shp_path)

        if source.mode == ImportMode.SPLIT_BY_VOLTAGE:
            result = self._import_split_voltage_substations(source.shp_path)
            return int(result) if isinstance(result, int) else sum(result.values())

        imported = 0
        for _field_names, raw_props, geometry in iter_shapefile_features(source.shp_path):
            properties = normalize_electricity_gis_properties(layer_id, raw_props)
            name = electricity_gis_feature_name(layer_id, properties)
            insert_electricity_gis_feature(layer_id, name, properties, geometry)
            imported += 1
        return imported

    def _import_split_voltage_substations(
        self,
        shp_path: Path,
        *,
        accumulate: bool = False,
    ) -> dict[str, int] | int:
        counts = {
            'power-gis-substations-66': 0,
            'power-gis-substations-230': 0,
            'power-gis-substations-400': 0,
        }
        for _field_names, raw_props, geometry in iter_shapefile_features(shp_path):
            voltage = voltage_from_classification(
                str(raw_props.get('تصنيف') or raw_props.get('تصني_1') or '')
            )
            if voltage == 66:
                target_layer = 'power-gis-substations-66'
            elif voltage == 400:
                target_layer = 'power-gis-substations-400'
            elif voltage == 230:
                target_layer = 'power-gis-substations-230'
            else:
                continue
            properties = normalize_electricity_gis_properties(target_layer, raw_props)
            name = electricity_gis_feature_name(target_layer, properties)
            insert_electricity_gis_feature(target_layer, name, properties, geometry)
            counts[target_layer] += 1
        if accumulate:
            return counts
        return sum(counts.values())

    def _import_point_series_line(self, layer_id: str, shp_path: Path, *, voltage_kv: int | None = None) -> int:
        geometry = line_geometry_from_point_series_shapefile(shp_path)
        if geometry is None:
            self.stdout.write(self.style.WARNING(f'Skipped empty segment: {shp_path.name}'))
            return 0
        if voltage_kv is None:
            spec = ELECTRICITY_GIS_LAYER_BY_ID.get(layer_id)
            voltage_kv = spec.voltage_kv if spec else 0
        properties = segment_line_properties(layer_id, shp_path, voltage_kv=voltage_kv)
        name = electricity_gis_feature_name(layer_id, properties)
        insert_electricity_gis_feature(layer_id, name, properties, geometry)
        return 1
