from __future__ import annotations

from pyproj import Transformer

SYRIA_LAT_RANGE = (32.0, 37.6)
SYRIA_LON_RANGE = (35.4, 42.5)

# Rainfall sheets use mixed UTM zones. Above this northing, ambiguous rows are
# in the eastern Jazira (Hasakah) rather than western Syria.
_JAZIRA_UTM_NORTHING = 4_050_000


def _in_syria(lat: float, lon: float) -> bool:
    return (
        SYRIA_LAT_RANGE[0] <= lat <= SYRIA_LAT_RANGE[1]
        and SYRIA_LON_RANGE[0] <= lon <= SYRIA_LON_RANGE[1]
    )


def _transform(epsg: int, x: float, y: float) -> tuple[float, float]:
    transformer = Transformer.from_crs(epsg, 4326, always_xy=True)
    lon, lat = transformer.transform(float(x), float(y))
    return lat, lon


def _normalize_utm(x: float, y: float) -> tuple[float, float]:
    """Fix common spreadsheet typos in Syrian dam/rainfall UTM rows."""
    easting, northing = float(x), float(y)
    # Truncated northing: 363658 should be 3636580 (missing trailing digit).
    if northing < 1_000_000 and 200_000 <= easting <= 900_000:
        scaled = northing * 10
        if 3_000_000 <= scaled <= 4_500_000:
            return easting, scaled
    # Inflated northing: 36181446 should be 3618144 (extra trailing digit).
    if northing > 4_500_000 and 200_000 <= easting <= 900_000:
        scaled = northing / 10
        if 3_000_000 <= scaled <= 4_500_000:
            return easting, scaled
    return easting, northing


def utm_to_wgs84(x: float, y: float) -> tuple[float | None, float | None]:
    if x is None or y is None:
        return None, None

    x, y = _normalize_utm(x, y)
    lat36, lon36 = _transform(32636, x, y)
    lat37, lon37 = _transform(32637, x, y)
    in36 = _in_syria(lat36, lon36)
    in37 = _in_syria(lat37, lon37)

    if in36 and in37:
        if lon36 <= 36.0 and lon37 >= 41.5:
            if float(y) >= _JAZIRA_UTM_NORTHING:
                return round(lat37, 6), round(lon37, 6)
            return round(lat36, 6), round(lon36, 6)
        if 35.3 <= lon36 <= 37.0 and lon37 >= 40.5:
            return round(lat37, 6), round(lon37, 6)

    for epsg in (32636, 32637):
        lat, lon = _transform(epsg, x, y)
        if _in_syria(lat, lon):
            return round(lat, 6), round(lon, 6)

    lat, lon = lat36, lon36
    return round(lat, 6), round(lon, 6)
