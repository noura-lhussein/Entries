from __future__ import annotations

from django.core.management.base import BaseCommand

from water.drinking_water_station_classifier import classify_drinking_water_station
from water.map_layers import sync_drinking_water_map_layer
from water.models import DrinkingWaterStation


class Command(BaseCommand):
    help = 'Classify drinking water stations for Power BI-style operational filters.'

    def handle(self, *args, **options):
        updated = 0
        for station in DrinkingWaterStation.objects.iterator():
            attrs = classify_drinking_water_station(
                station_code=station.station_code,
                name=station.name,
                incident_date=station.incident_date,
            )
            changed = False
            for field, value in attrs.items():
                if getattr(station, field) != value:
                    setattr(station, field, value)
                    changed = True
            if changed:
                station.save(update_fields=list(attrs.keys()))
                updated += 1

        sync_stats = sync_drinking_water_map_layer()
        self.stdout.write(
            self.style.SUCCESS(
                f'Classified {updated} drinking water stations. '
                f'Map layer synced: {sync_stats["imported"]} features.',
            ),
        )
