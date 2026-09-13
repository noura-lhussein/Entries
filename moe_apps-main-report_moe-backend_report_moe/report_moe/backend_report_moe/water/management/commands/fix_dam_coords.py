from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand

from water.coordinates import utm_to_wgs84
from water.models import Dam


class Command(BaseCommand):
    help = 'Recompute dam latitude/longitude from stored UTM coordinates.'

    def handle(self, *args, **options):
        updated = 0
        for dam in Dam.objects.exclude(utm_x__isnull=True).exclude(utm_y__isnull=True):
            lat, lon = utm_to_wgs84(float(dam.utm_x), float(dam.utm_y))
            if lat is None or lon is None:
                continue
            new_lat = Decimal(str(lat))
            new_lon = Decimal(str(lon))
            if dam.latitude == new_lat and dam.longitude == new_lon:
                continue
            old_lat, old_lon = dam.latitude, dam.longitude
            dam.latitude = new_lat
            dam.longitude = new_lon
            dam.save(update_fields=['latitude', 'longitude'])
            updated += 1
            self.stdout.write(
                f'  {dam.governorate} / {dam.name}: '
                f'({old_lat}, {old_lon}) -> ({new_lat}, {new_lon})',
            )

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} dam coordinates.'))
