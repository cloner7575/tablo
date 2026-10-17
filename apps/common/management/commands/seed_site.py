"""Seed the public catalogue from the bundled reviewed data and images."""

from apps.common.management.commands.import_industry_content import (
    Command as ImportIndustryCommand,
)


class Command(ImportIndustryCommand):
    help = (
        "Seed the site with 12 sign types, 11 photographed examples and "
        "7 business categories. Repeatable and offline; no fake member accounts."
    )
