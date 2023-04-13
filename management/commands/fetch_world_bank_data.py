from django.core.management.base import BaseCommand

from plugins.consortial_billing import utils, logic

from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):

    help = """
           Gets data from the World Bank API.
           Takes an indicator code such as NY.GNP.PCAP.CD or PA.NUS.FCRF
           """

    def add_arguments(self, parser):
        parser.add_argument('indicator', type=str)

    def handle(self, *args, **options):
        indicator = options['indicator']
        for year in logic.last_five_years():
            status_code = utils.fetch_world_bank_data(indicator, year)
            if status_code == 200:
                logger.info(
                    self.style.SUCCESS(
                        f'Got new {year} data'
                    )
                )
            else:
                logger.info(
                    self.style.WARNING(
                        f'Could not get {year} data'
                    )
                )
