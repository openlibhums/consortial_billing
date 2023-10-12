from django.core.management.base import BaseCommand

from plugins.consortial_billing import utils as supporter_utils

from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):

    help = """
           Creates demo bands for display
           """

    def handle(self, *args, **options):

        saved_file = supporter_utils.update_demo_band_data()
        logger.info(
            self.style.SUCCESS(
                f'Saved demo band data:\n{saved_file}'
            )
        )
