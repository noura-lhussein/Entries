from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEFAULT_PASSWORD = 'Demo@2026!'

# Sector demo users: read + write for their sector only.
DEMO_USERS = (
    {
        'email': 'admin@moe.gov.sy',
        'full_name': 'MOE Portal Admin',
        'is_staff': True,
        'is_superuser': True,
        'is_admin': True,
        'sectors': 'all',
    },
    {
        'email': 'water@moe.gov.sy',
        'full_name': 'Water Sector Operator',
        'is_staff': False,
        'is_admin': False,
        'sectors': ['water'],
    },
    {
        'email': 'oil@moe.gov.sy',
        'full_name': 'Petroleum Operator',
        'is_staff': False,
        'is_admin': False,
        'sectors': ['oil_gas'],
    },
    {
        'email': 'electricity@moe.gov.sy',
        'full_name': 'Electricity Operator',
        'is_staff': False,
        'is_admin': False,
        'sectors': ['electricity'],
    },
    {
        'email': 'geology@moe.gov.sy',
        'full_name': 'Geology & Mineral Resources Operator',
        'is_staff': False,
        'is_admin': False,
        'sectors': ['mineral'],
    },
)


def _apply_user_spec(user: User, spec: dict, password: str) -> None:
    user.full_name = spec['full_name']
    user.is_active = True
    user.is_staff = spec['is_staff']
    user.is_superuser = bool(spec.get('is_superuser', False))
    user.is_admin = spec['is_admin']
    if spec['sectors'] == 'all':
        user.grant_full_portal_access()
    else:
        # view + write for the assigned sector(s)
        user.can_view_info = True
        user.can_write_info = True
        user.portal_sectors = list(spec['sectors'])
        user.apply_portal_sectors()
    user.set_password(password)
    user.save()


class Command(BaseCommand):
    help = (
        'Create or update demo portal users with sector RBAC: '
        'admin (all), water, oil, electricity, geology (each with view+write).'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=DEFAULT_PASSWORD,
            help=f'Password for all demo users (default: {DEFAULT_PASSWORD}).',
        )
        parser.add_argument(
            '--only',
            type=str,
            default='',
            help='Comma-separated emails to seed (default: all demo users).',
        )

    def handle(self, *args, **options):
        password = options['password']
        only = {
            part.strip().lower()
            for part in (options['only'] or '').split(',')
            if part.strip()
        }

        for spec in DEMO_USERS:
            email = spec['email']
            if only and email not in only:
                continue

            user, created = User.objects.get_or_create(
                email=email,
                defaults={'full_name': spec['full_name']},
            )
            _apply_user_spec(user, spec, password)
            action = 'Created' if created else 'Updated'
            scope = 'all sectors' if spec['sectors'] == 'all' else ', '.join(spec['sectors'])
            self.stdout.write(
                self.style.SUCCESS(f'{action} {email} ({scope}) password={password}')
            )
