import time

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from plugins.consortial_billing import models

from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):

    help = """
           Tries to autofill RORs based on strict matching
           criteria, using the affiliation parameter approach:
           https://ror.readme.io/docs/matching#affiliation-parameter-approach
           Only saves if --save is passed.
           """

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Check all, not just the missing ones (default).',
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save the matched ROR if the supporter did not have one.',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Save the matched ROR even if the supporter had one already.',
        )

    def handle(self, *args, **options):
        if options['all']:
            supporters = models.Supporter.objects.all()
        else:
            supporters = models.Supporter.objects.filter(ror='')
        for supporter in supporters:
            time.sleep(.1)
            try:
                existing_ror = supporter.ror
                ror = supporter.get_ror(
                    save=options['save'],
                    overwrite=options['overwrite'],
                )
                if ror:
                    if existing_ror:
                        if ror == existing_ror:
                            message = f'Existing confirmed: { existing_ror }'
                        elif options['overwrite']:
                            message = f'Existing replaced: { existing_ror } => { ror }'
                        else:
                            message = f'New found: { ror }; left existing: { existing_ror }'
                    elif options['save']:
                        message = f'New saved: { ror }'
                    else:
                        message = f'New found but not saved: { ror }.'
                    logger.info(self.style.SUCCESS(message))
                else:
                    logger.warning(
                        self.style.WARNING(
                            f'No ROR found for { str(supporter.id).rjust(3) } - { supporter.name }'
                        )
                    )
            except ValidationError:
                pass
