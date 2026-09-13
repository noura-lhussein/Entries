import json
import urllib.error
import urllib.parse
import urllib.request

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..map_geocode import active_geocode_params

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "MOE-Report/1.0 (budget map geocoding)"


class GeocodeSearchView(APIView):
    """Proxy search for OpenStreetMap Nominatim (respects usage policy via server User-Agent)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if len(query) < 2:
            return Response([])

        params = {
            "q": query,
            "format": "json",
            "limit": "8",
            "bounded": "0",
            **active_geocode_params(),
        }
        req = urllib.request.Request(
            f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}",
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return Response(
                {"detail": "Geocoding service unavailable."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        results = []
        for item in payload:
            lat = item.get("lat")
            lon = item.get("lon")
            if not lat or not lon:
                continue
            try:
                results.append(
                    {
                        "id": item.get("place_id"),
                        "name": item.get("display_name", ""),
                        "latitude": float(lat),
                        "longitude": float(lon),
                    }
                )
            except (TypeError, ValueError):
                continue

        return Response(results)
