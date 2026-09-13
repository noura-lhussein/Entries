from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand

from water.coordinates import utm_to_wgs84
from water.models import RainfallStation


class Command(BaseCommand):
    help = 'Recompute rainfall station latitude/longitude from stored UTM coordinates.'

    def handle(self, *args, **options):
        updated = 0
        for station in RainfallStation.objects.exclude(utm_x__isnull=True).exclude(utm_y__isnull=True):
            lat, lon = utm_to_wgs84(float(station.utm_x), float(station.utm_y))
            if lat is None or lon is None:
                continue
            new_lat = Decimal(str(lat))
            new_lon = Decimal(str(lon))
            if station.latitude == new_lat and station.longitude == new_lon:
                continue
            old_lat, old_lon = station.latitude, station.longitude
            station.latitude = new_lat
            station.longitude = new_lon
            station.save(update_fields=['latitude', 'longitude'])
            updated += 1
            self.stdout.write(
                f'  {station.governorate} / {station.name}: '
                f'({old_lat}, {old_lon}) -> ({new_lat}, {new_lon})',
            )

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} station coordinates.'))
