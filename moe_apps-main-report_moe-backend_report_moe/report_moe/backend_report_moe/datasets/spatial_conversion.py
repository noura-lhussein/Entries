from __future__ import annotations

import io
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import shapefile
from pyproj import CRS, Transformer

from .models import Dataset

WGS84 = 'EPSG:4326'
SYRIA_UTM_FALLBACK = 'EPSG:32637'
COORD_PRECISION = 5
MAX_LINE_VERTICES = 400
MAX_RING_VERTICES = 200
MAX_3D_FEATURES_PER_SLICE = 8000


def _slugify(value: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return slug[:80] or 'layer'


def _looks_like_wgs84(bbox: tuple[float, float, float, float]) -> bool:
    xmin, ymin, xmax, ymax = bbox
    return (
        -180 <= xmin <= 180
        and -180 <= xmax <= 180
        and -90 <= ymin <= 90
        and -90 <= ymax <= 90
    )


def _resolve_transformer(shp_path: Path, bbox: tuple[float, float, float, float]) -> Transformer | None:
    prj_path = shp_path.with_suffix('.prj')
    if prj_path.exists():
        try:
            source = CRS.from_wkt(prj_path.read_text(encoding='utf-8', errors='replace'))
            if source == CRS.from_epsg(4326):
                return None
            return Transformer.from_crs(source, WGS84, always_xy=True)
        except Exception:
            pass

    if _looks_like_wgs84(bbox):
        return None

    try:
        return Transformer.from_crs(SYRIA_UTM_FALLBACK, WGS84, always_xy=True)
    except Exception:
        return None


def _transform_point(x: float, y: float, transformer: Transformer | None) -> list[float]:
    if transformer is None:
        return [round(x, COORD_PRECISION), round(y, COORD_PRECISION)]
    lon, lat = transformer.transform(x, y)
    return [round(lon, COORD_PRECISION), round(lat, COORD_PRECISION)]


def _decimate_coords(coords: list[list[float]], max_vertices: int) -> list[list[float]]:
    if len(coords) <= max_vertices:
        return coords
    step = max(1, len(coords) // max_vertices)
    simplified = [coords[index] for index in range(0, len(coords), step)]
    if simplified[-1] != coords[-1]:
        simplified.append(coords[-1])
    return simplified


def _simplify_geometry(geometry: dict[str, Any]) -> dict[str, Any]:
    geom_type = geometry.get('type')
    if geom_type == 'LineString':
        geometry['coordinates'] = _decimate_coords(geometry['coordinates'], MAX_LINE_VERTICES)
        return geometry
    if geom_type == 'MultiLineString':
        geometry['coordinates'] = [
            _decimate_coords(line, MAX_LINE_VERTICES)
            for line in geometry['coordinates']
        ]
        return geometry
    if geom_type == 'Polygon':
        geometry['coordinates'] = [
            _decimate_coords(ring, MAX_RING_VERTICES)
            for ring in geometry['coordinates']
        ]
        return geometry
    if geom_type == 'MultiPolygon':
        geometry['coordinates'] = [
            [_decimate_coords(ring, MAX_RING_VERTICES) for ring in polygon]
            for polygon in geometry['coordinates']
        ]
        return geometry
    return geometry


def _shape_to_geojson(shape: shapefile._Shape, transformer: Transformer | None) -> dict[str, Any] | None:
    if shape.shapeType == shapefile.NULL:
        return None

    if shape.shapeType in (shapefile.POINT, shapefile.POINTZ, shapefile.POINTM):
        return {
            'type': 'Point',
            'coordinates': _transform_point(shape.points[0][0], shape.points[0][1], transformer),
        }

    if shape.shapeType in (shapefile.POLYLINE, shapefile.POLYLINEZ, shapefile.POLYLINEM):
        if len(shape.parts) <= 1:
            return {
                'type': 'LineString',
                'coordinates': [
                    _transform_point(x, y, transformer)
                    for x, y in shape.points
                ],
            }
        lines: list[list[list[float]]] = []
        parts = list(shape.parts) + [len(shape.points)]
        for index in range(len(shape.parts)):
            segment = shape.points[parts[index] : parts[index + 1]]
            lines.append([_transform_point(x, y, transformer) for x, y in segment])
        return {'type': 'MultiLineString', 'coordinates': lines}

    if shape.shapeType in (shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM):
        rings: list[list[list[float]]] = []
        parts = list(shape.parts) + [len(shape.points)]
        for index in range(len(shape.parts)):
            ring = [
                _transform_point(x, y, transformer)
                for x, y in shape.points[parts[index] : parts[index + 1]]
            ]
            if len(ring) >= 4:
                rings.append(ring)
        if not rings:
            return None
        if len(rings) == 1:
            return {'type': 'Polygon', 'coordinates': rings}
        return {'type': 'MultiPolygon', 'coordinates': [[ring] for ring in rings]}

    return None


def _record_to_dict(fields: list[Any], record: tuple[Any, ...]) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for field, value in zip(fields, record, strict=False):
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace')
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        props[field] = value
    return props


def _shapefile_to_feature_collection(shp_path: Path) -> dict[str, Any]:
    reader = shapefile.Reader(str(shp_path), encoding='utf-8')
    field_names = [field[0] for field in reader.fields[1:]]
    transformer = _resolve_transformer(shp_path, tuple(reader.bbox))

    features: list[dict[str, Any]] = []
    for shape, record in zip(reader.shapes(), reader.records(), strict=False):
        geometry = _shape_to_geojson(shape, transformer)
        if geometry is None:
            continue
        features.append(
            {
                'type': 'Feature',
                'properties': _record_to_dict(field_names, record),
                'geometry': _simplify_geometry(geometry),
            }
        )

    return {'type': 'FeatureCollection', 'features': features}


def _discover_shapefiles(root: Path) -> list[Path]:
    discovered: list[Path] = []
    for shp_path in sorted(root.rglob('*.shp')):
        if shp_path.with_suffix('.dbf').exists():
            discovered.append(shp_path)
    return discovered


def _cap_feature_collection(geojson: dict[str, Any], max_features: int = MAX_3D_FEATURES_PER_SLICE) -> dict[str, Any]:
    features = geojson.get('features') or []
    if len(features) <= max_features:
        return geojson
    step = max(1, (len(features) + max_features - 1) // max_features)
    capped = features[::step][:max_features]
    return {**geojson, 'features': capped}


def _shapefile_slice(shp_path: Path, *, prefix: str = '') -> dict[str, Any]:
    label = shp_path.stem
    if prefix:
        label = f'{prefix} — {label}'
    geojson = _cap_feature_collection(_shapefile_to_feature_collection(shp_path))
    return {
        'id': _slugify(label),
        'label': label,
        'kind': 'geojson',
        'geojson': geojson,
    }


def _slices_from_shapefile_path(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == '.zip':
        work_dir = Path(tempfile.mkdtemp(prefix='dataset-shp-'))
        try:
            with zipfile.ZipFile(path) as archive:
                archive.extractall(work_dir)
            shapefiles = _discover_shapefiles(work_dir)
            if not shapefiles:
                raise ValueError('ZIP archive does not contain a valid shapefile (.shp + .dbf).')
            prefix = path.stem
            return [_shapefile_slice(shp_path, prefix=prefix if len(shapefiles) > 1 else '') for shp_path in shapefiles]
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    if path.suffix.lower() != '.shp':
        raise ValueError('Unsupported spatial file type for shapefile conversion.')

    if not path.with_suffix('.dbf').exists():
        raise ValueError('Shapefile is missing its .dbf companion file.')

    return [_shapefile_slice(path)]


def _zip_entry_kind(names: list[str]) -> str | None:
    normalized = [name.lower() for name in names if not name.endswith('/')]
    if any(name.endswith('.kml') for name in normalized):
        return 'kml'
    if any(name.endswith('.shp') for name in normalized):
        return 'shp'
    if any(name.endswith('.geojson') for name in normalized):
        return 'geojson'
    return None


def _zip_archive_kind(path: Path) -> str | None:
    if path.suffix.lower() != '.zip' or not path.exists():
        return None

    with zipfile.ZipFile(path) as archive:
        return _zip_entry_kind(archive.namelist())


_ZIP_KIND_FORMAT = {
    'shp': 'SHP',
    'kml': 'KML',
    'geojson': 'GeoJSON',
}


def infer_zip_archive_format(*, path: Path | None = None, data: bytes | None = None) -> str | None:
    kind = None
    if path is not None and path.suffix.lower() == '.zip' and path.exists():
        with zipfile.ZipFile(path) as archive:
            kind = _zip_entry_kind(archive.namelist())
    elif data is not None:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                kind = _zip_entry_kind(archive.namelist())
        except zipfile.BadZipFile:
            return None
    if not kind:
        return None
    return _ZIP_KIND_FORMAT.get(kind)


def is_shapefile_spatial_dataset(dataset: Dataset) -> bool:
    if not dataset.source_file:
        return False

    source_path = Path(dataset.source_file.path)
    filename = dataset.source_file.name.rsplit('/', 1)[-1].lower()
    if filename.endswith('.shp'):
        return True

    formats = {str(value).upper() for value in (dataset.resource_formats or [])}
    if 'SHP' in formats and 'KML' not in formats and 'KMZ' not in formats:
        return True

    if filename.endswith('.zip'):
        archive_kind = _zip_archive_kind(source_path)
        if archive_kind == 'shp':
            return True
        if archive_kind == 'kml':
            return False
        if 'SHP' in formats:
            return True
        if 'KML' in formats or 'KMZ' in formats:
            return False
        return 'shp' in filename

    return False


def build_dataset_spatial_slices(dataset: Dataset) -> list[dict[str, Any]]:
    if not dataset.source_file:
        raise ValueError('Dataset has no source file.')

    source_path = Path(dataset.source_file.path)
    if not source_path.exists():
        raise ValueError('Dataset source file is missing on disk.')

    return build_spatial_slices_from_path(source_path)


def build_spatial_slices_from_path(source_path: Path) -> list[dict[str, Any]]:
    if not source_path.exists():
        raise ValueError('Spatial file is missing on disk.')
    return _slices_from_shapefile_path(source_path)


def is_shapefile_file(path: Path, filename: str | None = None) -> bool:
    name = (filename or path.name).lower()
    if name.endswith('.shp'):
        return True
    if name.endswith('.zip'):
        return _zip_archive_kind(path) == 'shp' or 'shp' in name
    return False
