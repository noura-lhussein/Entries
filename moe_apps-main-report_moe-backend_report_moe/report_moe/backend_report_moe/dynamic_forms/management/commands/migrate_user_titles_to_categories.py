"""
Migrate legacy UserTitle rows into UserTitleCategory.

For each user, collects distinct categories of their assigned titles and creates
UserTitleCategory rows. Titles without a category are reported and skipped.

Usage:
  python manage.py migrate_user_titles_to_categories
  python manage.py migrate_user_titles_to_categories --apply
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import UserTitle, UserTitleCategory


class Command(BaseCommand):
    help = "Migrate UserTitle assignments into UserTitleCategory (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write UserTitleCategory rows. Default is dry-run.",
        )

    def handle(self, *args, **options):
        apply = bool(options["apply"])
        created = 0
        skipped_existing = 0
        uncategorized: list[str] = []

        by_user: dict[int, set[int]] = {}
        for ut in UserTitle.objects.select_related("title").iterator():
            title = ut.title
            if not title or not title.category_id:
                uncategorized.append(
                    f"user={ut.user_id} title_id={ut.title_id} name={getattr(title, 'name', '?')}"
                )
                continue
            by_user.setdefault(ut.user_id, set()).add(int(title.category_id))

        for user_id, category_ids in by_user.items():
            for category_id in category_ids:
                exists = UserTitleCategory.objects.filter(
                    user_id=user_id, category_id=category_id
                ).exists()
                if exists:
                    skipped_existing += 1
                    continue
                if apply:
                    with transaction.atomic():
                        UserTitleCategory.objects.get_or_create(
                            user_id=user_id, category_id=category_id
                        )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would create' if not apply else 'Created'}={created} "
                f"skipped_existing={skipped_existing} "
                f"uncategorized_title_links={len(uncategorized)} "
                f"mode={'APPLY' if apply else 'DRY-RUN'}"
            )
        )
        for row in uncategorized[:30]:
            self.stdout.write(self.style.WARNING(f"  uncategorized: {row}"))
        if len(uncategorized) > 30:
            self.stdout.write(
                self.style.WARNING(f"  ... and {len(uncategorized) - 30} more")
            )
