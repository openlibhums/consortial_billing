from django.core.management.base import BaseCommand
from django.core.management import call_command

from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):

    help = """
           Installs example data from example.json
           """

    def handle(self, *args, **options):

        call_command('loaddata', 'src/plugins/consortial_billing/example.json')
        logger.info(
            self.style.SUCCESS(
                f'Loaded example data'
            )
        )
