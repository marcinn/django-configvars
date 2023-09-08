from django.conf import settings
from django.core.management.base import BaseCommand

from ... import get_config_variables


class Command(BaseCommand):
    help = "Dump easysettings config"

    def add_arguments(self, parser):
        parser.add_argument(
            "--comments",
            action="store_true",
            help="Add comments to variables (if available)",
        )
        parser.add_argument(
            "--changed", action="store_true", help="Show only changed variables"
        )
        parser.add_argument(
            "--defaults",
            action="store_true",
            help="Show default values instead of current",
        )

    def handle(self, *args, **options):
        info = options["comments"]
        for var in get_config_variables():
            value = getattr(settings, var.name, None)
            if options["changed"] and not var.default == value:
                continue
            if options["defaults"]:
                value = var.default

            comment = ""
            if info:
                desc = var.desc
                if desc:
                    comment = f"  # {desc}"
            print(f"{var.name} = {repr(value)}{comment}")
