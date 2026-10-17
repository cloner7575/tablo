from argparse import ArgumentParser

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.common.industry_services import refresh_industry_content


class Command(BaseCommand):
    help = "Install attributed signage examples without fake accounts or prices."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--archive-demo",
            action="store_true",
            help="Archive exact seed_demo identities on a DEBUG preview only.",
        )

    def handle(self, *args: object, **options: object) -> None:
        if options["archive_demo"] and not settings.DEBUG:
            raise CommandError("Demo archival is only enabled on a DEBUG preview.")
        stats = refresh_industry_content(archive_demo=bool(options["archive_demo"]))
        self.stdout.write(self.style.SUCCESS(str(stats)))
