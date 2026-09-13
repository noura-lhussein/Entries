"""Default runserver port for report_moe: 8001."""

from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticfilesRunserverCommand,
)


class Command(StaticfilesRunserverCommand):
    default_port = '8001'
