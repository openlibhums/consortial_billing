from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from plugins.consortial_billing import models, forms

from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):

    help = """
           Calculates new supporter fees based on current data.
           Only saves if --save is passed.
           """

    def add_arguments(self, parser):
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save the new fee, replacing the old'
        )

    def handle(self, *args, **options):
        for supporter in models.Supporter.objects.all():
            try:
                old_band = supporter.band
                if old_band.fixed_fee:
                    logger.warning(
                        self.style.WARNING(
                            'Fixed fee needing manual updating: '
                            f'{str(supporter.id).rjust(3)} - {supporter.name}'
                        )
                    )
                    continue
                new_band_form = forms.BandForm({
                    'size': old_band.size,
                    'level': old_band.level,
                    'country': old_band.country,
                    'currency': old_band.currency,
                })
                if new_band_form.is_valid():
                    new_band = new_band_form.save(commit=options['save'])
                    if old_band == new_band:
                        continue
                else:
                    raise AttributeError
            except AttributeError:
                logger.warning(
                    self.style.WARNING(
                        'Not enough data to recalculate band for '
                        f'{str(supporter.id).rjust(3)} - {supporter.name}'
                    )
                )
                continue
            try:
                if options['save']:
                    models.OldBand.objects.get_or_create(supporter=supporter, band=old_band)
                    supporter.band = new_band
                    supporter.save()
                    status = 'Saved new fee: '
                else:
                    status = 'New fee (not saved): '
                logger.info(
                    self.style.SUCCESS(
                        status +
                        f'{str(old_band.fee).rjust(5)} {old_band.currency} -> '
                        f'{str(new_band.fee).rjust(5)} {new_band.currency} '
                        f'for {supporter.name}.'
                    )
                )
                if new_band.warnings:
                    logger.warning(
                        self.style.WARNING(
                            f'{str(supporter.id).rjust(3)} - {supporter.name}:'
                            + new_band.warnings,
                        )
                    )
            except ValidationError:
                logger.warning(
                    self.style.WARNING(
                        'Could not calculate fee for '
                        f'{str(supporter.id).rjust(3)} - {supporter.name}'
                    )
                )
