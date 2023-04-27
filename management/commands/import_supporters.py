import csv
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.utils import timezone

from plugins.consortial_billing import models, logic

from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):

    help = """
            Imports supporter data from CSV.
            Expected headers, in any order:
                name - string
                active - True or False
                band__level__name - string
                band__country - ISO 3166-1 Alpha 2 code
                band__currency__code - 3-letter currency code
                band__currency__region - 3-letter country code
                    corresponding to currency in World Bank data
                band__size__name - string
                band__size__description - string
                band__fee - number
           """

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=str,
            help='path to CSV file',
        )

    def handle(self, *args, **options):
        with open(options['file']) as file_ref:
            reader = csv.DictReader(file_ref)
            for row in tqdm(reader):
                level, created = models.SupportLevel.objects.get_or_create(
                    name=row.get('band__level__name'),
                )
                size, created = models.SupporterSize.objects.get_or_create(
                    name=row.get('band__size__name'),
                    description=row.get('band__size__description'),
                )
                country = row.get('band__country')
                currency, created = models.Currency.objects.get_or_create(
                    code=row.get('band__currency__code'),
                    region=row.get('band__currency__region'),
                )
                fee_string = row.get('band__fee')
                if fee_string:
                    fee = int(fee_string)
                else:
                    fee = 0
                billing_agent = logic.determine_billing_agent(country)
                band, created = models.Band.objects.get_or_create(
                    level=level,
                    size=size,
                    country=country,
                    currency=currency,
                    fee=fee,
                    warnings='',
                    billing_agent=billing_agent,
                    datetime__year=timezone.now().year,
                    display=True,
                )
                active = True if row.get('active') == 'True' else False
                supporter, created = models.Supporter.objects.get_or_create(
                    band=band,
                    name=row.get('name'),
                    active=active,
                    display=True,
                    country=country,
                )
