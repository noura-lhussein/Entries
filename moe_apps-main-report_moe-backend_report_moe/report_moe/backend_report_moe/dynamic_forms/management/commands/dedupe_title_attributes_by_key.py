"""
Merge duplicate Attribute rows on a Title that share the same `key`, then delete
the extras. Info rows on duplicate attributes are moved to the canonical row
(lower id); when the canonical already has the same (attribute, row_key) pair,
duplicate Info is dropped only when value and confirmed agree.

Usage:
  python manage.py dedupe_title_attributes_by_key
  python manage.py dedupe_title_attributes_by_key --apply
  python manage.py dedupe_title_attributes_by_key --title-code electricity.national --apply
  python manage.py dedupe_title_attributes_by_key --delete-empty-keys --apply
"""

from __future__ import annotations

from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count

from dynamic_forms.models import Attribute, Info, Title

DEFAULT_TITLE_CODE = 'electricity.national'


class Command(BaseCommand):
    help = (
        'Merge duplicate attributes that share the same key on one Title; '
        'reassign Info rows to the canonical attribute (lowest id).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--title-code',
            default=DEFAULT_TITLE_CODE,
            help=f'Title.code to clean (default: {DEFAULT_TITLE_CODE}).',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply merges and deletes (default is dry-run).',
        )
        parser.add_argument(
            '--delete-empty-keys',
            action='store_true',
            help='Also delete attributes with an empty key on this title (e.g. test fields).',
        )

    def handle(self, *args, **options):
        apply = bool(options['apply'])
        title_code = (options['title_code'] or '').strip()
        title = Title.objects.filter(code=title_code, deleted=False).first()
        if title is None:
            raise CommandError(f'Title with code={title_code!r} not found.')

        attrs = list(Attribute.objects.filter(title=title).order_by('id'))
        self.stdout.write(
            f'Title id={title.id}: {title.name} (code={title.code})')
        self.stdout.write(f'Attributes before: {len(attrs)}')

        by_key: dict[str, list[Attribute]] = defaultdict(list)
        empty_key: list[Attribute] = []
        for attr in attrs:
            key = (attr.key or '').strip()
            if key:
                by_key[key].append(attr)
            else:
                empty_key.append(attr)

        dup_groups = {k: group for k,
                      group in by_key.items() if len(group) > 1}
        self.stdout.write(f'Duplicate key groups: {len(dup_groups)}')
        if empty_key:
            self.stdout.write(f'Empty-key attributes: {len(empty_key)}')

        stats = {
            'attrs_deleted': 0,
            'info_moved': 0,
            'info_deleted': 0,
            'info_skipped': 0,
            'skipped': [],
        }

        def merge_pair(canonical: Attribute, duplicate: Attribute) -> None:
            if canonical.id == duplicate.id:
                return
            self.stdout.write(
                f'  merge attr {duplicate.id} ({duplicate.label!r}) → {canonical.id} ({canonical.label!r})'
            )
            for info in Info.objects.filter(attribute=duplicate).order_by('id'):
                if info.row_key is not None:
                    existing = Info.objects.filter(
                        attribute=canonical, row_key=info.row_key,
                    ).first()
                    if existing:
                        if (
                            existing.value == info.value
                            and existing.confirmed == info.confirmed
                        ):
                            stats['info_deleted'] += 1
                            if apply:
                                info.delete()
                        else:
                            stats['info_skipped'] += 1
                            stats['skipped'].append(
                                f'attr {duplicate.id}→{canonical.id} row_key={info.row_key} '
                                f'(canonical value={existing.value!r} vs {info.value!r})'
                            )
                        continue
                stats['info_moved'] += 1
                if apply:
                    info.attribute = canonical
                    info.save(update_fields=['attribute'])

            stats['attrs_deleted'] += 1
            if apply:
                duplicate.delete()

        with transaction.atomic():
            for key, group in sorted(dup_groups.items()):
                ordered = sorted(group, key=lambda a: a.id)
                canonical = ordered[0]
                self.stdout.write(
                    f'Key {key}: keep id={canonical.id}, drop {len(ordered) - 1}')
                for duplicate in ordered[1:]:
                    merge_pair(canonical, duplicate)

            if options['delete_empty_keys'] and empty_key:
                for attr in empty_key:
                    info_count = Info.objects.filter(attribute=attr).count()
                    self.stdout.write(
                        f'  delete empty-key attr {attr.id} ({attr.label!r}) '
                        f'[{info_count} Info rows CASCADE]'
                    )
                    stats['attrs_deleted'] += 1
                    if apply:
                        attr.delete()

            if not apply:
                transaction.set_rollback(True)

        self.stdout.write('')
        self.stdout.write(
            f'Attributes to remove: {stats["attrs_deleted"]}, '
            f'Info moved: {stats["info_moved"]}, '
            f'Info dropped (duplicate row_key): {stats["info_deleted"]}, '
            f'Info skipped (conflict): {stats["info_skipped"]}'
        )
        for line in stats['skipped'][:15]:
            self.stdout.write(self.style.WARNING(f'  skipped: {line}'))
        if len(stats['skipped']) > 15:
            self.stdout.write(f'  ... and {len(stats["skipped"]) - 15} more')

        remaining = Attribute.objects.filter(title=title).count()
        dup_remaining = (
            Attribute.objects.filter(title=title)
            .exclude(key='')
            .values('key')
            .annotate(n=Count('id'))
            .filter(n__gt=1)
            .count()
        )

        if apply:
            self.stdout.write(self.style.SUCCESS(
                f'Done. Attributes after: {remaining}, duplicate key groups left: {dup_remaining}'
            ))
        else:
            self.stdout.write(
                'Dry run only. Re-run with --apply to apply changes.')
