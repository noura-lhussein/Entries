"""GeoDjango / GDAL configuration for native Windows and macOS runs."""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path
from typing import Any


def use_geodjango() -> bool:
    # Default false for local Windows dev without GDAL; set true when OSGeo4W is configured.
    return os.getenv('USE_GEODJANGO', 'false').lower() in ('1', 'true', 'yes')


def _newest_dll(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern), key=lambda path: path.name, reverse=True)
    return matches[0] if matches else None


def discover_osgeo4w_bin() -> Path | None:
    roots: list[Path] = []
    if root := os.getenv('OSGEO4W_ROOT', '').strip():
        roots.append(Path(root))
    if sys.platform == 'win32':
        for pattern in (r'C:\OSGeo4W64*', r'C:\OSGeo4W*', r'D:\OSGeo4W64*', r'D:\OSGeo4W*'):
            roots.extend(Path(match) for match in sorted(glob.glob(pattern), reverse=True))
        roots.extend((Path(r'C:\OSGeo4W64'), Path(r'C:\OSGeo4W'), Path(r'D:\OSGeo4W64'), Path(r'D:\OSGeo4W')))

    seen: set[str] = set()
    for root in roots:
        key = str(root).lower()
        if key in seen:
            continue
        seen.add(key)
        bin_dir = root / 'bin'
        if bin_dir.is_dir() and _newest_dll(bin_dir, 'gdal3*.dll'):
            return bin_dir
    return None


def configure_geodjango(settings: dict[str, Any]) -> dict[str, str]:
    """
    Set GDAL_LIBRARY_PATH / GEOS_LIBRARY_PATH on the settings module.
    Returns resolved paths when found.
    """
    gdal_path = os.getenv('GDAL_LIBRARY_PATH', '').strip()
    geos_path = os.getenv('GEOS_LIBRARY_PATH', '').strip()

    bin_dir: Path | None = None
    if not gdal_path or not geos_path:
        bin_dir = discover_osgeo4w_bin()
        if bin_dir:
            if not gdal_path:
                gdal_dll = _newest_dll(bin_dir, 'gdal3*.dll')
                if gdal_dll:
                    gdal_path = str(gdal_dll)
            if not geos_path:
                geos_dll = _newest_dll(bin_dir, 'geos_c*.dll') or _newest_dll(bin_dir, 'geos*.dll')
                if geos_dll:
                    geos_path = str(geos_dll)

    if not gdal_path or not geos_path:
        return {}

    settings['GDAL_LIBRARY_PATH'] = gdal_path
    settings['GEOS_LIBRARY_PATH'] = geos_path

    if bin_dir:
        os.environ['PATH'] = str(bin_dir) + os.pathsep + os.environ.get('PATH', '')
        root = bin_dir.parent
        gdal_data = root / 'share' / 'gdal'
        proj_lib = root / 'share' / 'proj'
        if gdal_data.is_dir():
            os.environ.setdefault('GDAL_DATA', str(gdal_data))
        if proj_lib.is_dir():
            os.environ.setdefault('PROJ_LIB', str(proj_lib))

    return {
        'GDAL_LIBRARY_PATH': gdal_path,
        'GEOS_LIBRARY_PATH': geos_path,
    }
