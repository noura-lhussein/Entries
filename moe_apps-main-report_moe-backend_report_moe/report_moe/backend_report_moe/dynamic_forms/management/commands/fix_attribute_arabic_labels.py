"""
Persist Arabic Attribute.label for all titles (keep technical key in Attribute.key).

Usage:
  python manage.py fix_attribute_arabic_labels
  python manage.py fix_attribute_arabic_labels --dry-run
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.form_schema import apply_arabic_label_to_attribute
from dynamic_forms.models import Attribute


class Command(BaseCommand):
    help = (
        'Rewrite English/technical Attribute.label values to Arabic for all titles; '
        'preserve metric keys in Attribute.key.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report changes without writing to the database.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = bool(options['dry_run'])
        updated = 0
        skipped = 0
        for attr in Attribute.objects.select_related('title').order_by('title_id', 'id'):
            before_label = attr.label
            before_key = attr.key
            changed = apply_arabic_label_to_attribute(attr, save=not dry_run)
            if changed:
                updated += 1
                title_name = attr.title.name if attr.title_id else '—'
                self.stdout.write(
                    f"  [{title_name}] {before_label!r} → {attr.label!r}"
                    + (f" (key={attr.key or before_key})" if (attr.key or before_key) else '')
                )
                if dry_run:
                    # Restore in-memory state for dry-run clarity
                    attr.label = before_label
                    attr.key = before_key
            else:
                skipped += 1

        if dry_run:
            transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Dry-run: would update' if dry_run else 'Updated'} {updated} attributes "
                f"(unchanged={skipped})."
            )
        )
