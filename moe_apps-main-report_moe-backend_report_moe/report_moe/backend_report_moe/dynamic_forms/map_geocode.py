"""Map geocoding region presets — change ACTIVE_MAP_REGION to switch search defaults."""

MAP_REGIONS = {
    "syria": {
        "countrycodes": "sy",
        "viewbox": "35.72,37.32,42.35,32.31",
    },
    "palestine": {
        "countrycodes": "ps",
        "viewbox": "34.17,32.55,35.55,31.25",
    },
}

ACTIVE_MAP_REGION = "syria"


def active_geocode_params() -> dict[str, str]:
    region = MAP_REGIONS.get(ACTIVE_MAP_REGION, MAP_REGIONS["syria"])
    return {
        "countrycodes": region["countrycodes"],
        "viewbox": region["viewbox"],
        "accept-language": "ar,en",
    }
