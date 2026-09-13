from __future__ import annotations

from django.core.management.base import BaseCommand

from water.map_layers import sync_drinking_water_map_layer


class Command(BaseCommand):
    help = 'Sync drinking water stations from water_drinkingwaterstation into gis_water_feature.'

    def handle(self, *args, **options):
        stats = sync_drinking_water_map_layer()
        self.stdout.write(
            self.style.SUCCESS(
                f'Synced {stats["imported"]} drinking water stations to map layer water-drinking-stations.',
            ),
        )
