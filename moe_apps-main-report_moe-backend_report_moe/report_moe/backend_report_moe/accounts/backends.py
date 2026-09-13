"""Email authentication for report_moe.

Keeps the legacy fallbacks the shared backend carried: real accounts still exist
whose email is a synthesised placeholder (`user1@legacy.report-moe.local`), and
users type the bare local-part they signed up with rather than a full address. The
ranking rule below also stays, since after the auth split "prefer the report_moe
account" is simply what this table is.

moeds has its own copy, deliberately stripped of all of this.
"""

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

_LEGACY_LOCAL = re.compile(r'[^a-zA-Z0-9._-]+')


class EmailBackend(ModelBackend):
    """Authenticate by email, or by username matching the email local-part."""

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        User = get_user_model()
        identifier = email or username or kwargs.get(User.USERNAME_FIELD)
        if not identifier or password is None:
            return None

        identifier = str(identifier).strip()
        users = list(self._candidate_users(User, identifier))
        if not users:
            User().set_password(password)
            return None

        def _rank(user) -> tuple[int, int]:
            email = (user.email or '').lower()
            # Prefer report_moe-flavoured addresses when several share a local-part.
            if email.endswith(('@rep.com', '@report-moe.local', '@legacy.report-moe.local')):
                priority = 0
            elif 'report' in email:
                priority = 1
            else:
                priority = 2
            return (priority, user.id)

        users.sort(key=_rank)
        for user in users:
            if getattr(user, 'deleted', False):
                continue
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

    def _candidate_users(self, User, identifier: str):
        emails = self._candidate_emails(identifier)
        query = Q()
        for candidate in emails:
            query |= Q(email__iexact=candidate)

        # Bare username: also match any email whose local-part equals it
        # e.g. "admin" -> admin@rep.com, admin@moe.gov.sy, ...
        if '@' not in identifier:
            local = _LEGACY_LOCAL.sub('_', identifier).strip('._-') or identifier
            query |= Q(email__istartswith=f'{local}@')
            query |= Q(email__istartswith=f'{identifier}@')

        return User.objects.filter(query).order_by('id')

    def _candidate_emails(self, identifier: str) -> list[str]:
        identifier = identifier.strip()
        if not identifier:
            return []
        if '@' in identifier:
            return [identifier]

        local = _LEGACY_LOCAL.sub('_', identifier).strip('._-') or 'user'
        return [
            identifier,
            f'{local}@legacy.report-moe.local',
            f'{local}@report-moe.local',
            f'{identifier}@legacy.report-moe.local',
            f'{identifier}@report-moe.local',
            f'{identifier}@rep.com',
        ]

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
