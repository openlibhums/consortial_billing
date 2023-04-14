__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

from plugins.consortial_billing.tests import test_models

CB = 'plugins.consortial_billing'


class CommandTests(test_models.TestCaseWithData):

    def test_fetch_world_bank_data_no_args(self):
        with self.assertRaises(CommandError):
            call_command('fetch_world_bank_data')

    @patch(f'{CB}.utils.fetch_world_bank_data', return_value=200)
    @patch(f'{CB}.management.commands.fetch_world_bank_data.logger.info')
    def test_fetch_world_bank_data_with_indicator(self, info, utils_fetch):
        call_command('fetch_world_bank_data', self.fake_indicator)
        utils_fetch.assert_called()
        self.assertIn(self.fake_indicator, utils_fetch.call_args.args)
        info.assert_called()

    @patch(f'{CB}.forms.BandForm.save')
    @patch(f'{CB}.management.commands.calculate_all_fees.logger.info')
    @patch(f'{CB}.management.commands.calculate_all_fees.logger.warning')
    def test_calculate_all_fees_no_args(
        self,
        warning,
        info,
        band_form_save,
    ):
        band_form_save.return_value = self.band_other_one
        call_command('calculate_all_fees')
        band_form_save.assert_called_with(commit=False)
        info.assert_called()
        warning.assert_not_called()

    @patch(f'{CB}.models.Band.save')
    @patch(f'{CB}.forms.BandForm.save')
    @patch(f'{CB}.models.Supporter.save')
    @patch(f'{CB}.management.commands.calculate_all_fees.logger.info')
    @patch(f'{CB}.management.commands.calculate_all_fees.logger.warning')
    def test_calculate_all_fees_save(
        self,
        warning,
        info,
        supporter_save,
        band_form_save,
        band_save,
    ):
        band_save.return_value = self.band_other_one
        band_form_save.return_value = self.band_other_one
        supporter_save.return_value = self.supporter_one
        call_command('calculate_all_fees', '--save')
        band_save.assert_called()
        band_form_save.assert_called_with(commit=False)
        supporter_save.assert_called()
        info.assert_called()
        warning.assert_not_called()
